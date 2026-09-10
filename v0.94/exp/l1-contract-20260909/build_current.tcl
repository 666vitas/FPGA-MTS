# One Project-mode build from the current XPR; add independent runs only.
# input_redpitaya.xpr.snapshot preserves the pre-build project for auditing.
set root E:/new/fpga_lock/v94
set evidence [file dirname [file normalize [info script]]]
set project_path [file join $root v0.94 project redpitaya.xpr]
set synth_name l1_contract_synth_20260909
set impl_name l1_contract_impl_20260909
if {[version -short] ne "2020.1"} { error "Vivado 2020.1 required" }
open_project $project_path
if {[get_property TOP [get_filesets sources_1]] ne "red_pitaya_top"} { error "top mismatch" }
if {[get_property PART [current_project]] ne "xc7z010clg400-1"} { error "part mismatch" }
set identity [open [file join $evidence current_build_identity.txt] w]
puts $identity "Vivado=[version -short]\nXPR=$project_path\nHEAD=[exec git -C $root rev-parse HEAD]"
puts $identity "Top=[get_property TOP [get_filesets sources_1]]\nPart=[get_property PART [current_project]]"
foreach prop {VERILOG_DEFINE INCLUDE_DIRS GENERIC} {
    puts $identity "$prop=[get_property $prop [get_filesets sources_1]]"
}
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
create_run $synth_name -flow [get_property FLOW [get_runs synth_1]] \
    -strategy [get_property STRATEGY [get_runs synth_1]] -constrset constrs_1
clone_steps synth_1 $synth_name
create_run $impl_name -parent_run $synth_name -flow [get_property FLOW [get_runs impl_1]] \
    -strategy [get_property STRATEGY [get_runs impl_1]] -constrset constrs_1
clone_steps impl_1 $impl_name
launch_runs $synth_name -jobs 2 -dir [file join $evidence build]
wait_on_run $synth_name
if {![string match "*Complete*" [get_property STATUS [get_runs $synth_name]]]} { error "synthesis failed" }
launch_runs $impl_name -to_step route_design -jobs 2 -dir [file join $evidence build]
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
write_checkpoint [file join $evidence current_routed.dcp]
puts "CURRENT_BUILD_COMPLETE_NO_BITSTREAM"
close_project
exit
