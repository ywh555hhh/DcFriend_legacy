#!/bin/bash

# 定义源目录和目标目录
SRC_DIR="src"
TEST_DIR="tests"

# 遍历 src 目录下的所有 .py 文件
# -type f 表示只查找文件
# -name "*.py" 表示查找以 .py 结尾的文件
# -not -name "__init__.py" 表示排除 __init__.py 文件
find "$SRC_DIR" -type f -name "*.py" -not -name "__init__.py" | while read -r src_file; do
    
    # 将 src/path/to/file.py 转换为 tests/path/to/test_file.py
    relative_path="${src_file#$SRC_DIR/}"
    test_file_path="$TEST_DIR/$relative_path"
    
    # 获取测试文件所在的目录
    test_dir=$(dirname "$test_file_path")
    
    # 构造最终的测试文件名
    base_name=$(basename "$relative_path" .py)
    final_test_file="$test_dir/test_$base_name.py"
    
    # 如果测试目录不存在，则创建它
    mkdir -p "$test_dir"
    
    # 如果测试文件还不存在，则创建它并写入一个基本的模板
    if [ ! -f "$final_test_file" ]; then
        echo "Creating test file: $final_test_file"
        # 写入一个简单的 pytest 模板
        cat <<EOL > "$final_test_file"
import pytest

# TODO: Add tests for ${src_file}

def test_placeholder():
    """A placeholder test to ensure the file is picked up by pytest."""
    assert True
EOL
    else
        echo "Test file already exists, skipping: $final_test_file"
    fi
done

echo "Test file structure mirroring complete."