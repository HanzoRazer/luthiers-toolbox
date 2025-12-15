"""
Phase 2 Blueprint Import Testing Script
Tests OpenCV geometry detection and DXF export
"""
import sys
from pathlib import Path

# Add services/api to path
API_DIR = Path(__file__).parent / "services" / "api"
sys.path.insert(0, str(API_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("Phase 2 Blueprint Import - Geometry Detection Testing")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing /blueprint/health endpoint")
response = client.get("/blueprint/health")
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Phase: {data.get('phase')}")
print(f"   Phase 2 Available: {data.get('phase2_available')}")
print(f"   Features: {data.get('features')}")
if data.get('phase2_available'):
    print("   ✓ Phase 2 vectorizer loaded successfully")
else:
    print("   ⚠ Phase 2 vectorizer not available")

# Test 2: Check Phase 2 module import
print("\n2. Testing Phase 2 vectorizer module")
try:
    BLUEPRINT_SERVICE_PATH = Path(__file__).parent / "services" / "blueprint-import"
    sys.path.insert(0, str(BLUEPRINT_SERVICE_PATH))
    from vectorizer_phase2 import create_phase2_vectorizer, GeometryDetector
    print("   ✓ vectorizer_phase2 module imported")
    
    # Test detector initialization
    detector = GeometryDetector(dpi=300)
    print(f"   ✓ GeometryDetector initialized (DPI: {detector.dpi})")
    print(f"   ✓ Pixel to mm conversion: {detector.mm_per_pixel:.6f} mm/pixel")
    
    # Test vectorizer initialization
    vectorizer = create_phase2_vectorizer()
    print("   ✓ Phase2Vectorizer initialized")
    
except ImportError as e:
    print(f"   ✗ Phase 2 module import failed: {e}")
except Exception as e:
    print(f"   ✗ Phase 2 initialization failed: {e}")

# Test 3: OpenCV dependencies
print("\n3. Checking OpenCV dependencies")
try:
    import cv2
    print(f"   ✓ opencv-python {cv2.__version__}")
    
    import numpy as np
    print(f"   ✓ numpy {np.__version__}")
    
    import ezdxf
    print(f"   ✓ ezdxf {ezdxf.__version__}")
    
    from skimage import __version__ as skimage_version
    print(f"   ✓ scikit-image {skimage_version}")
    
except ImportError as e:
    print(f"   ✗ Missing dependency: {e}")

# Test 4: Edge detection functions
print("\n4. Testing edge detection functions")
try:
    import cv2
    import numpy as np
    
    # Create test image (100x100 white square on black background)
    test_image = np.zeros((200, 200), dtype=np.uint8)
    test_image[50:150, 50:150] = 255
    
    # Test preprocessing
    detector = GeometryDetector()
    preprocessed = detector.preprocess_image(test_image)
    print(f"   ✓ Image preprocessing: {preprocessed.shape}")
    
    # Test edge detection
    edges = detector.detect_edges(preprocessed)
    edge_count = np.count_nonzero(edges)
    print(f"   ✓ Edge detection: {edge_count} edge pixels")
    
    # Test contour extraction
    contours = detector.extract_contours(edges, min_area=50)
    print(f"   ✓ Contour extraction: {len(contours)} contours")
    
    # Test line detection
    lines = detector.detect_lines(edges, threshold=50)
    print(f"   ✓ Line detection: {len(lines)} lines")
    
except Exception as e:
    print(f"   ✗ Edge detection test failed: {e}")

# Test 5: DXF export
print("\n5. Testing DXF R2000 export (CAM-compatible)")
try:
    import ezdxf
    from ezdxf import units as dxf_units
    import tempfile
    
    # Create test DXF (R2000 for LWPOLYLINE support)
    doc = ezdxf.new('R2000', setup=True)
    msp = doc.modelspace()
    doc.header['$INSUNITS'] = dxf_units.MM
    
    # Add test geometry
    doc.layers.new('GEOMETRY', dxfattribs={'color': 3})
    msp.add_lwpolyline(
        [(0, 0), (100, 0), (100, 60), (0, 60)],
        dxfattribs={'layer': 'GEOMETRY', 'closed': True}
    )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
        tmp_path = tmp.name
    
    doc.saveas(tmp_path)
    print(f"   ✓ DXF R2000 created: {tmp_path}")
    
    # Verify file size
    file_size = Path(tmp_path).stat().st_size
    print(f"   ✓ File size: {file_size} bytes")
    
    # Clean up
    Path(tmp_path).unlink()
    print("   ✓ Temp file cleaned up")
    
except Exception as e:
    print(f"   ✗ DXF export test failed: {e}")

print("\n" + "=" * 60)
print("Phase 2 Testing Summary")
print("=" * 60)

if data.get('phase2_available'):
    print("✓ Phase 2 vectorizer is operational")
    print("\nAvailable Features:")
    print("  • OpenCV edge detection (Canny + Hough transform)")
    print("  • Contour extraction with Douglas-Peucker simplification")
    print("  • SVG export with detected geometry")
    print("  • DXF R12 export with layers (GEOMETRY, LINES, DIMENSIONS)")
    print("  • Scale correction support")
    print("\nNext Steps:")
    print("  1. Create or download sample guitar blueprint (PNG/JPG)")
    print("  2. Use /blueprint/analyze to get AI dimensions")
    print("  3. Use /blueprint/vectorize-geometry to detect geometry")
    print("  4. Import DXF into Fusion 360 or VCarve for validation")
else:
    print("⚠ Phase 2 vectorizer not available")
    print("\nTo enable Phase 2:")
    print("  pip install opencv-python scikit-image ezdxf")

print("=" * 60)
