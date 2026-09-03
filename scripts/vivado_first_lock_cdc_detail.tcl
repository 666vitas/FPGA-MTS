# Vivado 2020.1 detailed analysis of the routed legacy daisy CDC paths.

set script_dir [file dirname [file normalize [info script]]]
set repo_root [file dirname $script_dir]
set project_path [file join $repo_root v0.94 project redpitaya.xpr]
set report_dir [file join $repo_root v0.94 timing_for_codex fresh_2026-09-02]
file mkdir $report_dir

open_project $project_path
open_run impl_1

help report_cdc

set adc_clock [get_clocks pll_adc_clk]
set par_clock [get_clocks par_clk]

report_timing -from $adc_clock -to $par_clock -delay_type max \
    -path_type full_clock_expanded -max_paths 200 -nworst 20 \
    -file [file join $report_dir 13_pll_adc_to_par_timing.rpt]
report_timing -from $par_clock -to $adc_clock -delay_type max \
    -path_type full_clock_expanded -max_paths 200 -nworst 20 \
    -file [file join $report_dir 14_par_to_pll_adc_timing.rpt]

if {[catch {
    report_cdc -details -from $adc_clock -to $par_clock \
        -file [file join $report_dir 15_pll_adc_to_par_cdc_detail.rpt]
} result]} {
    puts stderr "FIRST_LOCK_CDC_DETAIL_ERROR: pll_adc_clk to par_clk | $result"
    exit 1
}

if {[catch {
    report_cdc -details -from $par_clock -to $adc_clock \
        -file [file join $report_dir 16_par_to_pll_adc_cdc_detail.rpt]
} result]} {
    puts stderr "FIRST_LOCK_CDC_DETAIL_ERROR: par_clk to pll_adc_clk | $result"
    exit 1
}

puts "FIRST_LOCK_CDC_DETAIL_COMPLETE"
close_project
exit 0
