set root E:/new/fpga_lock/v94
set evidence E:/new/fpga_lock/v94/v0.94/exp/l1-candidate-20260911
set build_dir [file join $evidence build_nophys]
set synth_name l1_candidate_synth_20260911
set impl_name l1_candidate_impl_nophys_20260911
open_project [file join $root v0.94 project redpitaya.xpr]
proc clone_steps {from to} {
    foreach prop [list_property [get_runs $from]] {
        if {[regexp {^STEPS\..*\.(ARGS\.|IS_ENABLED$|TCL\.)} $prop]} {
            set_property $prop [get_property $prop [get_runs $from]] [get_runs $to]
        }
    }
}
if {[llength [get_runs $impl_name -quiet]]} { delete_runs [get_runs $impl_name] }
create_run $impl_name -parent_run [get_runs $synth_name] \
  -flow [get_property FLOW [get_runs impl_1]] \
  -strategy [get_property STRATEGY [get_runs impl_1]] -constrset constrs_1
clone_steps impl_1 $impl_name
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED 0 [get_runs $impl_name]
launch_runs $impl_name -to_step route_design -jobs 2 -dir $build_dir
wait_on_run $impl_name
puts "NOPHYS_STATUS=[get_property STATUS [get_runs $impl_name]]"
if {![string match "*Complete*" [get_property STATUS [get_runs $impl_name]]]} { error "implementation failed" }
open_run $impl_name
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
  -file [file join $evidence current_timing_summary_nophys.rpt]
check_timing -verbose -file [file join $evidence current_check_timing_nophys.rpt]
report_route_status -file [file join $evidence current_route_status_nophys.rpt]
report_drc -file [file join $evidence current_drc_nophys.rpt]
report_cdc -file [file join $evidence current_cdc_nophys.rpt]
report_methodology -file [file join $evidence current_methodology_nophys.rpt]
report_utilization -hierarchical -file [file join $evidence current_utilization_nophys.rpt]
write_checkpoint -force [file join $evidence current_routed_nophys.dcp]
close_project
exit
