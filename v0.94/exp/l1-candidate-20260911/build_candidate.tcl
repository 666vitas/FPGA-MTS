# Candidate implementation from the current XPR and current working tree.
# This run is independent of impl_1 and l1_contract_impl_20260909.
set root E:/new/fpga_lock/v94
set evidence [file dirname [file normalize [info script]]]
set project_path [file join $root v0.94 project redpitaya.xpr]
set build_dir [file join $evidence build]
set synth_name l1_candidate_synth_20260911
set impl_name l1_candidate_impl_20260911
if {[version -short] ne "2020.1"} { error "Vivado 2020.1 required" }
open_project $project_path
if {[get_property TOP [get_filesets sources_1]] ne "red_pitaya_top"} { error "top mismatch" }
if {[get_property PART [current_project]] ne "xc7z010clg400-1"} { error "part mismatch" }
set identity [open [file join $evidence current_build_identity.txt] w]
puts $identity "Vivado=[version -short]\nXPR=$project_path\nHEAD=[exec git -C $root rev-parse HEAD]"
puts $identity "Top=[get_property TOP [get_filesets sources_1]]\nPart=[get_property PART [current_project]]"
puts $identity "ENABLE_DAISY=0; DNA clock constraint=adc_clk/16"
puts $identity "Active synthesis compile order:"
foreach f [get_files -compile_order sources -used_in synthesis] { puts $identity [get_property NAME $f] }
close $identity
proc clone_steps {from to} {
    foreach prop [list_property [get_runs $from]] {
        if {[regexp {^STEPS\..*\.(ARGS\.|IS_ENABLED$|TCL\.)} $prop]} {
            set_property $prop [get_property $prop [get_runs $from]] [get_runs $to]
        }
    }
}
if {[llength [get_runs $synth_name -quiet]]} { delete_runs [get_runs $synth_name] }
if {[llength [get_runs $impl_name -quiet]]} { delete_runs [get_runs $impl_name] }
create_run $synth_name -flow [get_property FLOW [get_runs synth_1]] \
    -strategy [get_property STRATEGY [get_runs synth_1]] -constrset constrs_1
clone_steps synth_1 $synth_name
create_run $impl_name -parent_run $synth_name -flow [get_property FLOW [get_runs impl_1]] \
    -strategy [get_property STRATEGY [get_runs impl_1]] -constrset constrs_1
clone_steps impl_1 $impl_name
launch_runs $synth_name -jobs 2 -dir $build_dir
wait_on_run $synth_name
if {![string match "*Complete*" [get_property STATUS [get_runs $synth_name]]]} { error "synthesis failed" }
launch_runs $impl_name -to_step route_design -jobs 2 -dir $build_dir
wait_on_run $impl_name
if {![string match "*Complete*" [get_property STATUS [get_runs $impl_name]]]} { error "implementation failed" }
open_run $impl_name
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
    -file [file join $evidence current_timing_summary.rpt]
check_timing -verbose -file [file join $evidence current_check_timing.rpt]
report_route_status -file [file join $evidence current_route_status.rpt]
report_drc -file [file join $evidence current_drc.rpt]
report_cdc -file [file join $evidence current_cdc.rpt]
report_methodology -file [file join $evidence current_methodology.rpt]
report_utilization -hierarchical -file [file join $evidence current_utilization.rpt]
write_checkpoint -force [file join $evidence current_routed.dcp]
puts "CANDIDATE_ROUTE_COMPLETE_NO_BITSTREAM"
close_project
exit
