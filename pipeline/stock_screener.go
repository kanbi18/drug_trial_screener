package pipeline

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"os"
	"sort"
	"strconv"
)

var FMPAPIKey = os.Getenv("FMP_API_KEY")

var FMPIndustries = []string{
	"Biotechnology",
	"Drug Manufacturers - General",
	"Drug Manufacturers - Specialty & Generic",
}

var FMPScreenerURL = "https://financialmodelingprep.com/api/v3/stock-screener"

type fmpCompany struct {
	Symbol      string   `json:"symbol"`
	CompanyName string   `json:"companyName"`
	MarketCap   *float64 `json:"marketCap"`
	Sector      string   `json:"sector"`
	Industry    string   `json:"industry"`
	Exchange    string   `json:"exchange"`
}

func GetPublicBiotechList(maxMarketCap *float64, exchanges string) ([]Company, error) {
	if FMPAPIKey == "" {
		return nil, errors.New("FMP_API_KEY environment variable is not set")
	}

	all := map[string]Company{}
	for _, industry := range FMPIndustries {
		fmt.Printf("Fetching companies for industry: %s...\n", industry)
		q := url.Values{}
		q.Set("sector", "Healthcare")
		q.Set("industry", industry)
		q.Set("exchange", exchanges)
		q.Set("apikey", FMPAPIKey)
		if maxMarketCap != nil {
			q.Set("marketCapLowerThan", strconv.FormatInt(int64(*maxMarketCap), 10))
		}

		resp, err := HTTPClient.Get(FMPScreenerURL + "?" + q.Encode())
		if err != nil {
			return nil, err
		}
		if resp.StatusCode >= 400 {
			_ = resp.Body.Close()
			return nil, fmt.Errorf("fmp screener returned status %d", resp.StatusCode)
		}
		var items []fmpCompany
		if err := json.NewDecoder(resp.Body).Decode(&items); err != nil {
			_ = resp.Body.Close()
			return nil, err
		}
		_ = resp.Body.Close()

		fmt.Printf("  Found %d companies.\n", len(items))
		for _, item := range items {
			if item.Symbol == "" {
				continue
			}
			if _, exists := all[item.Symbol]; exists {
				continue
			}
			c := Company{
				Symbol:   item.Symbol,
				Name:     item.CompanyName,
				Sector:   item.Sector,
				Industry: item.Industry,
				Exchange: item.Exchange,
			}
			if item.MarketCap != nil {
				c.MarketCap = *item.MarketCap
			}
			all[item.Symbol] = c
		}
	}

	out := make([]Company, 0, len(all))
	for _, c := range all {
		out = append(out, c)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Symbol < out[j].Symbol })
	return out, nil
}
