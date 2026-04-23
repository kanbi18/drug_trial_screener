package pipeline

import (
	"fmt"
	"math"
	"sort"
	"strings"
)

var PhaseBaseRates = map[string]float64{
	"PHASE1": 0.08,
	"PHASE2": 0.15,
	"PHASE3": 0.58,
	"PHASE4": 0.90,
	"NA":     0.05,
}

type areaRule struct {
	Keywords []string
	Modifier float64
	Label    string
}

var therapeuticAreaRules = []areaRule{
	{[]string{"cancer", "tumor", "tumour", "carcinoma", "lymphoma", "leukemia", "melanoma", "sarcoma", "glioblastoma", "myeloma", "neoplasm", "oncology", "metastatic"}, -0.03, "Oncology"},
	{[]string{"orphan", "rare disease", "ultra-rare", "duchenne", "huntington", "sickle cell", "cystic fibrosis", "spinal muscular atrophy", "hemophilia", "fabry", "gaucher", "pompe"}, 0.05, "Rare / Orphan Disease"},
	{[]string{"alzheimer", "parkinson", "depression", "schizophrenia", "epilepsy", "migraine", "neuropathic", "multiple sclerosis", "als", "amyotrophic", "bipolar", "anxiety", "adhd", "autism", "neurodegenerat", "dementia", "cerebellar", "ataxia"}, -0.04, "CNS / Neurology"},
	{[]string{"hiv", "hepatitis", "influenza", "covid", "sars", "tuberculosis", "malaria", "antibiotic", "antiviral", "antifungal", "infection", "vaccine", "pneumonia", "sepsis"}, 0.02, "Infectious Disease"},
	{[]string{"cardiovascular", "heart failure", "hypertension", "atherosclerosis", "atrial fibrillation", "stroke", "thrombosis", "cholesterol", "triglyceride", "cardiac"}, -0.02, "Cardiovascular"},
	{[]string{"diabetes", "obesity", "metabolic", "nafld", "nash", "lipodystrophy", "hyperlipidemia", "thyroid"}, 0.00, "Metabolic / Endocrine"},
	{[]string{"autoimmune", "rheumatoid", "lupus", "psoriasis", "crohn", "ulcerative colitis", "inflammatory bowel", "eczema", "dermatitis", "ankylosing"}, 0.01, "Autoimmune / Inflammatory"},
}

var Weights = map[string]float64{
	"phase_base_rate":    0.30,
	"therapeutic_area":   0.15,
	"recruitment_status": 0.10,
	"enrollment_size":    0.10,
	"fda_approvals":      0.15,
	"market_cap_tier":    0.10,
	"multi_site":         0.10,
}

func GetBaseRate(phase string) float64 {
	if strings.TrimSpace(phase) == "" {
		return PhaseBaseRates["NA"]
	}
	phases := strings.Fields(strings.ToUpper(strings.ReplaceAll(phase, ",", " ")))
	best := PhaseBaseRates["NA"]
	for _, ph := range phases {
		if v, ok := PhaseBaseRates[ph]; ok {
			if v > best {
				best = v
			}
		}
	}
	return best
}

func DetectTherapeuticArea(title string, conditions []string) (string, float64) {
	text := strings.ToLower(strings.TrimSpace(title + " " + strings.Join(conditions, " ")))
	for _, rule := range therapeuticAreaRules {
		for _, kw := range rule.Keywords {
			if strings.Contains(text, kw) {
				return rule.Label, rule.Modifier
			}
		}
	}
	return "General", 0.0
}

func scorePhase(baseRate float64) float64 {
	return clamp(baseRate*100, 0, 100)
}

func scoreTherapeuticArea(modifier float64) float64 {
	return clamp(50+modifier*500, 0, 100)
}

func scoreRecruitment(status string) float64 {
	mapping := map[string]float64{
		"RECRUITING":              80,
		"NOT_YET_RECRUITING":      50,
		"ACTIVE_NOT_RECRUITING":   40,
		"ENROLLING_BY_INVITATION": 60,
	}
	if v, ok := mapping[status]; ok {
		return v
	}
	return 30
}

func scoreEnrollment(enrollmentCount *int) float64 {
	if enrollmentCount == nil || *enrollmentCount <= 0 {
		return 30
	}
	v := *enrollmentCount
	if v < 50 {
		return 35
	}
	if v < 200 {
		return 50
	}
	if v < 1000 {
		return 70
	}
	return 85
}

func scoreFDAApprovals(count *int) float64 {
	if count == nil {
		return 40
	}
	v := *count
	if v == 0 {
		return 25
	}
	if v <= 2 {
		return 50
	}
	if v <= 10 {
		return 70
	}
	return 90
}

func scoreMarketCap(marketCap *float64) float64 {
	if marketCap == nil || *marketCap <= 0 {
		return 30
	}
	capB := *marketCap / 1e9
	if capB < 0.5 {
		return 25
	}
	if capB < 2 {
		return 45
	}
	if capB < 10 {
		return 65
	}
	if capB < 50 {
		return 60
	}
	return 55
}

func scoreMultiSite(locationsCount int) float64 {
	if locationsCount <= 0 {
		return 30
	}
	if locationsCount == 1 {
		return 40
	}
	if locationsCount <= 10 {
		return 60
	}
	if locationsCount <= 50 {
		return 75
	}
	return 85
}

func CalculateReadinessScore(trial Trial, companyData *CompanyData) (int, float64, string, string) {
	if companyData == nil {
		companyData = &CompanyData{}
	}

	baseRate := GetBaseRate(trial.Phase)
	areaLabel, areaModifier := DetectTherapeuticArea(trial.Title, trial.Conditions)

	type scoreDesc struct {
		Score float64
		Desc  string
	}

	subScores := map[string]scoreDesc{
		"phase_base_rate":    {scorePhase(baseRate), fmt.Sprintf("Phase base rate %.0f%%", baseRate*100)},
		"therapeutic_area":   {scoreTherapeuticArea(areaModifier), fmt.Sprintf("%s area (%+.0f%%)", areaLabel, areaModifier*100)},
		"recruitment_status": {scoreRecruitment(trial.Status), fmt.Sprintf("Status: %s", fallbackString(trial.Status, "unknown"))},
		"enrollment_size":    {scoreEnrollment(trial.EnrollmentCount), fmt.Sprintf("Enrollment: %s", intPtrString(trial.EnrollmentCount))},
		"fda_approvals":      {scoreFDAApprovals(companyData.FDAApprovalCount), fmt.Sprintf("Prior FDA approvals: %s", optIntString(companyData.FDAApprovalCount))},
		"market_cap_tier":    {scoreMarketCap(companyData.MarketCap), "Market cap tier"},
		"multi_site":         {scoreMultiSite(trial.LocationsCount), fmt.Sprintf("Sites: %d", trial.LocationsCount)},
	}

	total := 0.0
	for key, w := range Weights {
		total += subScores[key].Score * w
	}
	readinessScore := int(math.Round(total))

	type weighted struct {
		Val  float64
		Desc string
	}
	ranked := make([]weighted, 0, len(Weights))
	for key, w := range Weights {
		ranked = append(ranked, weighted{Val: subScores[key].Score * w, Desc: subScores[key].Desc})
	}
	sort.Slice(ranked, func(i, j int) bool { return ranked[i].Val > ranked[j].Val })

	top := []string{}
	for i := 0; i < len(ranked) && i < 3; i++ {
		top = append(top, ranked[i].Desc)
	}
	rationale := strings.Join(top, "; ")

	return readinessScore, baseRate, areaLabel, rationale
}

func fallbackString(v, def string) string {
	if strings.TrimSpace(v) == "" {
		return def
	}
	return v
}

func intPtrString(v *int) string {
	if v == nil {
		return "N/A"
	}
	return fmt.Sprintf("%d", *v)
}

func clamp(v, minVal, maxVal float64) float64 {
	if v < minVal {
		return minVal
	}
	if v > maxVal {
		return maxVal
	}
	return v
}

func optIntString(v *int) string {
	if v == nil {
		return "N/A"
	}
	return fmt.Sprintf("%d", *v)
}
