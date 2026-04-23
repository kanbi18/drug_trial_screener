package main

import (
	"flag"
	"fmt"
	"os"

	"research/internal/app"
)

func main() {
	capBillions := flag.Float64("cap", 10, "Maximum market cap in billions")
	flag.Parse()

	cfg := app.Config{
		Cap:       capBillions,
		Phase:     "all",
		OutputDir: ".",
		Format:    "csv",
	}
	if err := app.RunPipeline(cfg); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
