"""Create sample saw runs for dashboard testing"""
import json
from datetime import datetime, timedelta
from cnc_production.joblog.models import SawRunRecord, SawRunMeta, TelemetrySample
from cnc_production.joblog.storage import save_run, append_telemetry

print('=== Creating Sample Saw Runs ===')
print()

# Create 3 runs with different risk levels
runs_data = [
    {
        'risk_level': 'green',
        'load_range': (20, 35),
        'op_type': 'slice',
        'material': 'softwood',
        'blade': 'BLADE_10IN_40T',
        'samples': 15
    },
    {
        'risk_level': 'yellow', 
        'load_range': (70, 85),
        'op_type': 'batch',
        'material': 'hardwood',
        'blade': 'BLADE_10IN_60T',
        'samples': 20
    },
    {
        'risk_level': 'red',
        'load_range': (88, 96),
        'op_type': 'contour',
        'material': 'plywood',
        'blade': 'BLADE_12IN_80T',
        'samples': 25
    }
]

base_time = datetime.utcnow() - timedelta(hours=2)

for i, data in enumerate(runs_data):
    created = base_time + timedelta(minutes=i*30)
    run_id = f'run_{created.strftime("%Y%m%d_%H%M%S")}'
    
    meta = SawRunMeta(
        op_type=data['op_type'],
        machine_profile='SAW_LAB_01',
        material_family=data['material'],
        blade_id=data['blade'],
        safe_z_mm=5.0,
        depth_passes=1,
        total_length_mm=1200.0
    )
    
    run = SawRunRecord(
        run_id=run_id,
        status='completed',
        created_at=created,
        started_at=created,
        completed_at=created + timedelta(minutes=5),
        meta=meta,
        gcode='G90 G21 G1 X100 Y50 F1200 M30'
    )
    
    save_run(run)
    
    # Add telemetry samples
    min_load, max_load = data['load_range']
    load_step = (max_load - min_load) / data['samples']
    
    for j in range(data['samples']):
        sample = TelemetrySample(
            timestamp=created + timedelta(seconds=j*20),
            x_mm=float(j * 80),
            rpm_actual=3600,
            feed_actual_mm_min=1200.0,
            spindle_load_percent=min_load + j * load_step,
            vibration_mg=600.0 + j * 10,
            in_cut=True
        )
        append_telemetry(run_id, sample)
    
    print(f'✓ Created {data["risk_level"]} risk run: {run_id}')
    print(f'  - Load: {min_load:.0f}-{max_load:.0f}%')
    print(f'  - Material: {data["material"]}')
    print(f'  - Samples: {data["samples"]}')
    print()

print('✓✓ Sample data created!')
print()
print('Refresh the dashboard to see:')
print('  - 3 runs with different risk levels (green, yellow, red)')
print('  - Telemetry metrics visualization')
print('  - Risk classification and color coding')
