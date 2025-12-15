# services/api/tests/test_art_studio_bracing.py

"""
Tests for Art Studio Bracing API endpoints.

Endpoints tested:
    POST /api/art-studio/bracing/preview
    POST /api/art-studio/bracing/batch
    GET  /api/art-studio/bracing/presets
    POST /api/art-studio/bracing/export-dxf
    GET  /api/art-studio/bracing/dxf-versions
"""

import pytest
from fastapi.testclient import TestClient


class TestArtStudioBracingAPI:
    """Test Art Studio bracing endpoints."""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_preview_parabolic(self, client):
        """Test bracing preview with parabolic profile."""
        resp = client.post('/api/art-studio/bracing/preview', json={
            'profile_type': 'parabolic',
            'width_mm': 12.0,
            'height_mm': 8.0,
            'length_mm': 300.0,
            'density_kg_m3': 420.0
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Check section properties
        assert data['section']['profile_type'] == 'parabolic'
        assert data['section']['width_mm'] == 12.0
        assert data['section']['height_mm'] == 8.0
        assert data['section']['area_mm2'] == pytest.approx(63.36, rel=0.01)
        
        # Check mass (area × length × density / 1e9 × 1000)
        assert data['mass_grams'] == pytest.approx(7.98, rel=0.01)
        
        # Check stiffness estimate exists
        assert 'stiffness_estimate' in data
        assert data['stiffness_estimate'] > 0

    def test_preview_rectangular(self, client):
        """Test bracing preview with rectangular profile."""
        resp = client.post('/api/art-studio/bracing/preview', json={
            'profile_type': 'rectangular',
            'width_mm': 10.0,
            'height_mm': 6.0,
            'length_mm': 200.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Rectangular: area = width × height
        assert data['section']['area_mm2'] == pytest.approx(60.0, rel=0.01)

    def test_preview_triangular(self, client):
        """Test bracing preview with triangular profile."""
        resp = client.post('/api/art-studio/bracing/preview', json={
            'profile_type': 'triangular',
            'width_mm': 10.0,
            'height_mm': 8.0,
            'length_mm': 200.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Triangular: area = 0.5 × width × height
        assert data['section']['area_mm2'] == pytest.approx(40.0, rel=0.01)

    def test_preview_defaults(self, client):
        """Test bracing preview with default parameters."""
        resp = client.post('/api/art-studio/bracing/preview', json={})
        assert resp.status_code == 200
        data = resp.json()
        
        # Should use defaults
        assert data['section']['profile_type'] == 'parabolic'
        assert data['section']['width_mm'] == 12.0
        assert data['section']['height_mm'] == 8.0

    def test_presets_endpoint(self, client):
        """Test bracing presets endpoint."""
        resp = client.get('/api/art-studio/bracing/presets')
        assert resp.status_code == 200
        
        presets = resp.json()
        assert len(presets) >= 3
        
        # Check preset structure
        for preset in presets:
            assert 'id' in preset
            assert 'name' in preset
            assert 'description' in preset
            assert 'braces' in preset
            assert len(preset['braces']) > 0

    def test_presets_x_brace(self, client):
        """Test that X-brace preset exists with expected structure."""
        resp = client.get('/api/art-studio/bracing/presets')
        presets = resp.json()
        
        x_brace = next((p for p in presets if 'x-brace' in p['id'].lower()), None)
        assert x_brace is not None
        assert len(x_brace['braces']) == 2  # X-brace has 2 braces

    def test_batch_calculation(self, client):
        """Test batch bracing calculation."""
        resp = client.post('/api/art-studio/bracing/batch', json={
            'name': 'Test X-Brace',
            'braces': [
                {
                    'profile_type': 'parabolic',
                    'width_mm': 12.0,
                    'height_mm': 8.0,
                    'length_mm': 280.0,
                },
                {
                    'profile_type': 'parabolic',
                    'width_mm': 12.0,
                    'height_mm': 8.0,
                    'length_mm': 280.0,
                },
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        
        assert data['name'] == 'Test X-Brace'
        assert len(data['braces']) == 2
        assert data['totals']['count'] == 2
        assert data['totals']['total_mass_grams'] > 0
        
        # Both braces should have same mass
        assert data['braces'][0]['mass_grams'] == data['braces'][1]['mass_grams']

    def test_batch_mixed_profiles(self, client):
        """Test batch with mixed profile types."""
        resp = client.post('/api/art-studio/bracing/batch', json={
            'name': 'Mixed Bracing',
            'braces': [
                {'profile_type': 'rectangular', 'width_mm': 10.0, 'height_mm': 5.0, 'length_mm': 200.0},
                {'profile_type': 'triangular', 'width_mm': 8.0, 'height_mm': 6.0, 'length_mm': 180.0},
                {'profile_type': 'parabolic', 'width_mm': 12.0, 'height_mm': 8.0, 'length_mm': 250.0},
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        
        assert len(data['braces']) == 3
        assert data['braces'][0]['profile_type'] == 'rectangular'
        assert data['braces'][1]['profile_type'] == 'triangular'
        assert data['braces'][2]['profile_type'] == 'parabolic'


class TestBracingCalculatorFacade:
    """Test the bracing calculator facade directly."""

    def test_calculate_brace_section(self):
        from app.calculators.bracing_calc import BracingCalcInput, calculate_brace_section
        
        inp = BracingCalcInput(
            profile_type='parabolic',
            width_mm=12.0,
            height_mm=8.0,
        )
        result = calculate_brace_section(inp)
        
        assert result.profile_type == 'parabolic'
        assert result.area_mm2 == pytest.approx(63.36, rel=0.01)
        assert 'parabolic' in result.description.lower()

    def test_estimate_mass_grams(self):
        from app.calculators.bracing_calc import BracingCalcInput, estimate_mass_grams
        
        inp = BracingCalcInput(
            profile_type='rectangular',
            width_mm=10.0,
            height_mm=5.0,
            length_mm=200.0,
            density_kg_m3=420.0,
        )
        mass = estimate_mass_grams(inp)
        
        # volume = 10 × 5 × 200 = 10000 mm³ = 10e-6 m³
        # mass = 10e-6 × 420 × 1000 = 4.2 grams
        assert mass == pytest.approx(4.2, rel=0.01)

    def test_calculate_brace_set(self):
        from app.calculators.bracing_calc import BracingCalcInput, calculate_brace_set
        
        braces = [
            BracingCalcInput(profile_type='parabolic', width_mm=12.0, height_mm=8.0, length_mm=280.0),
            BracingCalcInput(profile_type='parabolic', width_mm=12.0, height_mm=8.0, length_mm=280.0),
        ]
        result = calculate_brace_set(braces)
        
        assert result['totals']['count'] == 2
        assert len(result['braces']) == 2
        assert result['totals']['total_mass_grams'] > 0


class TestBracingDxfExport:
    """Test DXF export endpoints."""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_export_dxf_r12(self, client):
        """Test DXF export with R12 (genesis version)."""
        resp = client.post('/api/art-studio/bracing/export-dxf', json={
            'braces': [
                {'name': 'X-Left', 'x_mm': -50, 'y_mm': 100, 'angle_deg': 45, 'length_mm': 280},
                {'name': 'X-Right', 'x_mm': 50, 'y_mm': 100, 'angle_deg': -45, 'length_mm': 280},
            ],
            'dxf_version': 'R12',
            'soundhole_diameter_mm': 100,
        })
        assert resp.status_code == 200
        assert resp.headers.get('x-dxf-version') == 'R12'
        assert resp.headers.get('x-brace-count') == '2'
        assert len(resp.content) > 1000  # Should have substantial content
        
        # Check DXF header
        content = resp.content.decode('utf-8')
        assert 'SECTION' in content
        assert 'HEADER' in content

    def test_export_dxf_r2000(self, client):
        """Test DXF export with R2000 version."""
        resp = client.post('/api/art-studio/bracing/export-dxf', json={
            'braces': [{'name': 'Test', 'x_mm': 0, 'y_mm': 0, 'length_mm': 200}],
            'dxf_version': 'R2000',
        })
        assert resp.status_code == 200
        assert resp.headers.get('x-dxf-version') == 'R2000'

    def test_export_dxf_r2010(self, client):
        """Test DXF export with R2010 (R18) version."""
        resp = client.post('/api/art-studio/bracing/export-dxf', json={
            'braces': [{'name': 'Test', 'x_mm': 0, 'y_mm': 0, 'length_mm': 200}],
            'dxf_version': 'R2010',
        })
        assert resp.status_code == 200
        assert resp.headers.get('x-dxf-version') == 'R2010'

    def test_export_dxf_alias_r18(self, client):
        """Test DXF export with R18 alias."""
        resp = client.post('/api/art-studio/bracing/export-dxf', json={
            'braces': [{'name': 'Test', 'x_mm': 0, 'y_mm': 0, 'length_mm': 200}],
            'dxf_version': 'R18',
        })
        assert resp.status_code == 200
        assert resp.headers.get('x-dxf-version') == 'R2010'  # R18 -> R2010

    def test_export_dxf_invalid_version(self, client):
        """Test DXF export with invalid version."""
        resp = client.post('/api/art-studio/bracing/export-dxf', json={
            'braces': [{'name': 'Test', 'x_mm': 0, 'y_mm': 0, 'length_mm': 200}],
            'dxf_version': 'R99',
        })
        assert resp.status_code == 400
        assert 'Invalid DXF version' in resp.json()['detail']

    def test_export_dxf_with_soundhole(self, client):
        """Test DXF export includes soundhole reference."""
        resp = client.post('/api/art-studio/bracing/export-dxf', json={
            'braces': [{'name': 'Test', 'x_mm': 0, 'y_mm': 0, 'length_mm': 200}],
            'soundhole_diameter_mm': 100,
            'soundhole_x_mm': 0,
            'soundhole_y_mm': 150,
        })
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert 'REFERENCE' in content  # Layer for soundhole

    def test_export_dxf_layers(self, client):
        """Test DXF export creates expected layers."""
        resp = client.post('/api/art-studio/bracing/export-dxf', json={
            'braces': [{'name': 'Test', 'x_mm': 0, 'y_mm': 0, 'length_mm': 200}],
            'include_centerlines': True,
            'include_outlines': True,
            'include_labels': True,
        })
        assert resp.status_code == 200
        content = resp.content.decode('utf-8')
        assert 'BRACES' in content
        assert 'CENTERLINES' in content
        assert 'LABELS' in content

    def test_dxf_versions_endpoint(self, client):
        """Test DXF versions listing endpoint."""
        resp = client.get('/api/art-studio/bracing/dxf-versions')
        assert resp.status_code == 200
        data = resp.json()
        
        assert data['default'] == 'R12'
        assert 'versions' in data
        assert len(data['versions']) == 7  # R12, R13, R14, R2000, R2004, R2007, R2010
        
        # Check R12 is marked as genesis/recommended
        r12 = next(v for v in data['versions'] if v['version'] == 'R12')
        assert r12['recommended'] is True
        assert r12['supports_lwpolyline'] is False

    def test_dxf_file_size_by_version(self, client):
        """Test that newer DXF versions produce larger files (more metadata)."""
        sizes = {}
        for ver in ['R12', 'R2000', 'R2010']:
            resp = client.post('/api/art-studio/bracing/export-dxf', json={
                'braces': [{'name': 'Test', 'x_mm': 0, 'y_mm': 0, 'length_mm': 200}],
                'dxf_version': ver,
            })
            sizes[ver] = len(resp.content)
        
        # R12 should be smallest (genesis - minimal metadata)
        assert sizes['R12'] < sizes['R2000']
        assert sizes['R2000'] < sizes['R2010']
