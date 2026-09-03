# Vivado 2020.1 Project Mode clean build and routed timing evidence.
# This script intentionally stops before write_bitstream.

set script_dir [file dirname [file normalize [info script]]]
set repo_root [file dirname $script_dir]
set project_path [file join $repo_root v0.94 project redpitaya.xpr]
set report_dir [file join $repo_root v0.94 timing_for_codex fresh_2026-09-02]
file mkdir $report_dir
set git_head [string trim [exec git -C $repo_root rev-parse HEAD]]

proc fail {message} {
    puts stderr "FIRST_LOCK_BUILD_ERROR: $message"
    exit 1
}

proc normalized_compile_sources {} {
    set result {}
    foreach source_obj [get_files -compile_order sources -used_in synthesis] {
        lappend result [file normalize [get_property NAME $source_obj]]
    }
    return $result
}

proc require_source {compile_sources expected_path} {
    set normalized_expected [file normalize $expected_path]
    if {[lsearch -exact $compile_sources $normalized_expected] < 0} {
        fail "active synthesis source missing: $normalized_expected"
    }
    puts "FIRST_LOCK_ACTIVE_SOURCE: $normalized_expected"
}

proc require_run_complete {run_name} {
    set run_status [get_property STATUS [get_runs $run_name]]
    set run_progress [get_property PROGRESS [get_runs $run_name]]
    puts "FIRST_LOCK_RUN_STATUS: $run_name | $run_status | $run_progress"
    if {![string match "*Complete*" $run_status]} {
        fail "$run_name did not complete: $run_status"
    }
}

proc optional_report {command_name command_args output_path} {
    if {[llength [info commands $command_name]] == 0} {
        puts "FIRST_LOCK_OPTIONAL_UNSUPPORTED: $command_name"
        return
    }
    set full_command [linsert $command_args 0 $command_name]
    lappend full_command -file $output_path
    if {[catch {uplevel #0 $full_command} result]} {
        puts "FIRST_LOCK_OPTIONAL_FAILED: $command_name | $result"
    } else {
        puts "FIRST_LOCK_OPTIONAL_WRITTEN: $output_path"
    }
}

if {![file exists $project_path]} {
    fail "project not found: $project_path"
}
if {$git_head ne "04937478807fc6a2d65a43129180649cbdf99967"} {
    fail "unexpected Git HEAD: $git_head"
}

set tool_version [version -short]
puts "FIRST_LOCK_VIVADO_VERSION: $tool_version"
if {![string match "2020.1*" $tool_version]} {
    fail "Vivado 2020.1 required, got $tool_version"
}

open_project $project_path
set actual_part [get_property PART [current_project]]
set actual_top [get_property TOP [get_filesets sources_1]]
puts "FIRST_LOCK_PROJECT: [file normalize $project_path]"
puts "FIRST_LOCK_PART: $actual_part"
puts "FIRST_LOCK_TOP: $actual_top"
if {$actual_part ne "xc7z010clg400-1"} {
    fail "unexpected part: $actual_part"
}
if {$actual_top ne "red_pitaya_top"} {
    fail "unexpected top: $actual_top"
}

update_compile_order -fileset sources_1
set compile_sources [normalized_compile_sources]
foreach source_name {
    red_pitaya_top.sv
    custom_register_bank.sv
    ramp_generator.sv
    laser_lock_core.sv
    mixer_core.sv
    lpf_core.sv
} {
    require_source $compile_sources [file join $repo_root v0.94 rtl $source_name]
}

set source_manifest [open [file join $report_dir 00_build_identity.txt] w]
puts $source_manifest "Vivado=$tool_version"
puts $source_manifest "Project=[file normalize $project_path]"
puts $source_manifest "Part=$actual_part"
puts $source_manifest "Top=$actual_top"
puts $source_manifest "GitHead=$git_head"
puts $source_manifest "Active synthesis compile order:"
foreach source_path $compile_sources {
    puts $source_manifest $source_path
}
close $source_manifest

# Exact clean targets authorized for this FIRST_LOCK run.
reset_run impl_1
reset_run synth_1

launch_runs synth_1
wait_on_run synth_1
require_run_complete synth_1

launch_runs impl_1 -to_step route_design
wait_on_run impl_1
require_run_complete impl_1
open_run impl_1

report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -max_paths 200 -nworst 50 \
    -file [file join $report_dir 01_timing_summary.rpt]
check_timing -verbose -file [file join $report_dir 02_check_timing.rpt]
report_clocks -file [file join $report_dir 03_clocks.rpt]
report_clock_interaction -file [file join $report_dir 04_clock_interaction.rpt]
report_utilization -hierarchical -file [file join $report_dir 05_utilization_hierarchical.rpt]
report_drc -file [file join $report_dir 06_drc.rpt]
report_timing -delay_type max -path_type full_clock_expanded \
    -max_paths 10 -nworst 1 -file [file join $report_dir 07_worst_setup_paths.rpt]
report_timing -delay_type min -path_type full_clock_expanded \
    -max_paths 10 -nworst 1 -file [file join $report_dir 08_worst_hold_paths.rpt]

optional_report report_cdc {} [file join $report_dir 09_cdc.rpt]
optional_report report_methodology {} [file join $report_dir 10_methodology.rpt]
optional_report report_design_analysis {-timing -setup -max_paths 10} \
    [file join $report_dir 11_design_analysis.rpt]

puts "FIRST_LOCK_REPORT_DIR: [file normalize $report_dir]"
puts "FIRST_LOCK_BUILD_COMPLETE_NO_BITSTREAM"
close_project
exit 0
