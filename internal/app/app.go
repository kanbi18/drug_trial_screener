package app

import (
	"errors"
	"flag"
	"fmt"
	"strconv"
	"strings"

	"research/pipeline"
)

type Config struct {
	Cap         *float64
	Phase       string
	OutputDir   string
	SkipScoring bool
	CompanyInfo bool
	Format      string
}

func ParseArgs(argv []string) (Config, error) {
	fs := flag.NewFlagSet("biotech-pipeline", flag.ContinueOnError)
	var cfg Config
	var capValue float64
	var hasCap bool

	fs.Func("cap", "Maximum market cap in billions", func(v string) error {
		n, err := strconv.ParseFloat(v, 64)
		if err != nil {
			return err
		}
		hasCap = true
		capValue = n
		return nil
	})
	fs.StringVar(&cfg.Phase, "phase", "all", "Comma-separated phases: 1,2,3 or all")
	fs.StringVar(&cfg.OutputDir, "output-dir", "./data", "Output directory")
	fs.BoolVar(&cfg.SkipScoring, "skip-scoring", false, "Skip readiness scoring")
	fs.BoolVar(&cfg.CompanyInfo, "company-info", false, "Generate company info table")
	fs.StringVar(&cfg.Format, "format", "csv", "Output format")

	if err := fs.Parse(argv); err != nil {
		return Config{}, err
	}
	if hasCap {
		cfg.Cap = &capValue
	}
	if cfg.Format != "csv" {
		return Config{}, errors.New("only csv format is currently supported")
	}
	return cfg, nil
}

func FilterTrialsByPhase(trials []pipeline.Trial, phaseArg string) []pipeline.Trial {
	if phaseArg == "all" {
		return trials
	}
	wanted := map[string]struct{}{}
	for _, p := range strings.Split(phaseArg, ",") {
		p = strings.TrimSpace(p)
		if p != "" {
			wanted["PHASE"+p] = struct{}{}
		}
	}
	if len(wanted) == 0 {
		return trials
	}

	filtered := make([]pipeline.Trial, 0, len(trials))
	for _, trial := range trials {
		phaseTokens := tokenizePhases(trial.Phase)
		keep := false
		for _, ph := range phaseTokens {
			if _, ok := wanted[ph]; ok {
				keep = true
				break
			}
		}
		if keep {
			filtered = append(filtered, trial)
		}
	}
	return filtered
}

func tokenizePhases(phase string) []string {
	phase = strings.ReplaceAll(phase, ",", " ")
	parts := strings.Fields(strings.ToUpper(phase))
	return parts
}

func Main(argv []string) error {
	args, err := ParseArgs(argv)
	if err != nil {
		return err
	}
	return RunPipeline(args)
}

func RunPipeline(args Config) error {
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("STEP 1: Screening biotech/pharma companies")
	fmt.Println(strings.Repeat("=", 60))

	var threshold *float64
	if args.Cap != nil {
		t := *args.Cap * 1e9
		threshold = &t
	}

	companies, err := pipeline.GetPublicBiotechList(threshold, "NYSE,NASDAQ,AMEX")
	if err != nil {
		return err
	}
	if len(companies) == 0 {
		fmt.Println("No companies found. Exiting.")
		return nil
	}

	var capLabel string
	if args.Cap != nil {
		if *args.Cap == float64(int(*args.Cap)) {
			capLabel = fmt.Sprintf("%dB", int(*args.Cap))
		} else {
			capLabel = fmt.Sprintf("%gB", *args.Cap)
		}
	}

	fmt.Printf("  Found %d companies.\n", len(companies))
	if _, err := pipeline.ExportCompanyListCSV(companies, args.OutputDir, ""); err != nil {
		return err
	}

	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("STEP 2: Fetching clinical trials from ClinicalTrials.gov")
	fmt.Println(strings.Repeat("=", 60))

	rawTrials, err := pipeline.FetchAllTrials(companies, nil)
	if err != nil {
		return err
	}
	fmt.Printf("  Fetched %d raw trials.\n", len(rawTrials))

	trials := FilterTrialsByPhase(rawTrials, args.Phase)
	if args.Phase != "all" {
		fmt.Printf("  After phase filter (%s): %d trials.\n", args.Phase, len(trials))
	}

	if !args.SkipScoring {
		fmt.Println()
		fmt.Println(strings.Repeat("=", 60))
		fmt.Println("STEP 3: Scoring trial readiness")
		fmt.Println(strings.Repeat("=", 60))

		fdaCache := map[string]int{}
		for _, company := range companies {
			cleanName := pipeline.CleanCompanyName(company.Name)
			if _, ok := fdaCache[cleanName]; !ok {
				count, _ := pipeline.GetFDAApprovalCount(cleanName)
				fdaCache[cleanName] = count
			}
		}

		marketCapBySymbol := map[string]float64{}
		for _, c := range companies {
			marketCapBySymbol[c.Symbol] = c.MarketCap
		}

		for i := range trials {
			mc := marketCapBySymbol[trials[i].Ticker]
			fda := fdaCache[trials[i].Company]
			companyData := pipeline.CompanyData{
				MarketCap:        &mc,
				FDAApprovalCount: &fda,
			}

			score, baseRate, area, rationale := pipeline.CalculateReadinessScore(trials[i], &companyData)
			trials[i].ReadinessScore = &score
			trials[i].BaseRate = &baseRate
			trials[i].TherapeuticArea = &area
			trials[i].ReadinessRationale = &rationale
			isMulti := trials[i].LocationsCount > 1
			trials[i].IsMultiSite = &isMulti
		}

		fmt.Printf("  Scored %d trials.\n", len(trials))
	} else {
		fmt.Println("\n  Skipping scoring (--skip-scoring).")
		for i := range trials {
			isMulti := trials[i].LocationsCount > 1
			trials[i].IsMultiSite = &isMulti
		}
	}

	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("STEP 4: Exporting results")
	fmt.Println(strings.Repeat("=", 60))

	if _, err := pipeline.ExportTrialsCSV(trials, args.OutputDir, "", capLabel); err != nil {
		return err
	}

	if args.CompanyInfo {
		fmt.Println()
		fmt.Println(strings.Repeat("=", 60))
		fmt.Println("STEP 5: Building company info table")
		fmt.Println(strings.Repeat("=", 60))

		companyTable, err := pipeline.BuildCompanyTable(companies, trials)
		if err != nil {
			return err
		}
		if _, err := pipeline.ExportCompaniesCSV(companyTable, args.OutputDir, ""); err != nil {
			return err
		}
	}

	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("DONE")
	fmt.Println(strings.Repeat("=", 60))
	return nil
}
