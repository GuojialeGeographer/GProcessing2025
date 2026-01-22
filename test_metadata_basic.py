"""
Basic test script for metadata module.
"""
import sys
sys.path.insert(0, '/Users/bruce/10_School/11_MSC-Politecnico di Milano/03-Third Sem-Archive/GProcessing/2025-2026/GProcessing2025/src')

from svipro.metadata import SamplingMetadata, MetadataSerializer, MetadataValidator, MetadataExporter
from shapely.geometry import box

# Test 1: Create metadata from scratch
print("Test 1: Creating metadata from scratch...")
try:
    metadata = SamplingMetadata(
        protocol_id="test_001",
        protocol_name="Test Protocol",
        description="Test description for metadata module",
        version="1.0.0",
        author="Test Author",
        institution="Politecnico di Milano"
    )
    print("✓ Metadata created successfully")
    print(f"  Protocol ID: {metadata.protocol_id}")
    print(f"  Protocol Name: {metadata.protocol_name}")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: Validate metadata
print("\nTest 2: Validating metadata...")
try:
    validator = MetadataValidator()
    is_valid, errors = validator.validate(metadata)
    if is_valid:
        print("✓ Metadata is valid")
    else:
        print(f"✗ Validation failed: {errors}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 3: Serialize to JSON
print("\nTest 3: Serializing to JSON...")
try:
    serializer = MetadataSerializer(format='json')
    json_str = serializer.to_json(metadata)
    print("✓ JSON serialization successful")
    print(f"  JSON length: {len(json_str)} characters")

    # Deserialize
    loaded = serializer.from_json(json_str)
    print("✓ JSON deserialization successful")
    print(f"  Loaded protocol ID: {loaded.protocol_id}")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 4: Serialize to YAML
print("\nTest 4: Serializing to YAML...")
try:
    serializer_yaml = MetadataSerializer(format='yaml')
    yaml_str = serializer_yaml.to_yaml(metadata)
    print("✓ YAML serialization successful")
    print(f"  YAML length: {len(yaml_str)} characters")

    # Deserialize
    loaded_yaml = serializer_yaml.from_yaml(yaml_str)
    print("✓ YAML deserialization successful")
    print(f"  Loaded protocol ID: {loaded_yaml.protocol_id}")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 5: Quick validate
print("\nTest 5: Quick validation...")
try:
    from svipro.metadata import quick_validate
    is_valid = quick_validate(metadata)
    if is_valid:
        print("✓ Quick validation passed")
    else:
        print("✗ Quick validation failed")
        sys.exit(1)
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 6: Export to multiple formats
print("\nTest 6: Exporting to multiple formats...")
try:
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = MetadataExporter()

        # Export JSON
        json_path = os.path.join(tmpdir, "test.json")
        exporter.export_json(metadata, json_path)
        print(f"✓ JSON exported to {json_path}")

        # Export YAML
        yaml_path = os.path.join(tmpdir, "test.yaml")
        exporter.export_yaml(metadata, yaml_path)
        print(f"✓ YAML exported to {yaml_path}")

        # Export CSV
        csv_path = os.path.join(tmpdir, "test.csv")
        exporter.export_csv(metadata, csv_path)
        print(f"✓ CSV exported to {csv_path}")

        # Export HTML
        html_path = os.path.join(tmpdir, "test.html")
        exporter.export_html_report(metadata, html_path)
        print(f"✓ HTML report exported to {html_path}")

except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("All tests passed! ✓")
print("="*50)
