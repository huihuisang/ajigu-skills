# 开发环境只读定位

根据已经安装的开发环境选择对应位置；不存在时跳过。清单用于调查，不代表这些目录可以整体删除，也不包含固定大小或回收量承诺。

## 常见位置

| 位置 | 内容与注意事项 |
| --- | --- |
| ~/Library/Developer/Xcode/DerivedData | 构建、索引及可能正在运行的 App；核对项目归属 |
| ~/Library/Developer/Xcode/iOS DeviceSupport | 真机调试支持文件；删除后可能需要重新准备 |
| ~/Library/Developer/XcodeBuildMCP/workspaces | 工具创建的工作区；先识别源码、未提交修改和仍在使用的路径 |
| ~/Library/Developer/XCTestDevices | 测试设备及其数据；APFS 克隆会影响 du 与实际回收量的关系 |
| ~/Library/Developer/CoreSimulator/Devices | 模拟器设备数据；使用系统工具调查状态 |
| ~/Library/Caches/org.swift.swiftpm | SwiftPM 缓存；核对是否属于活跃构建 |
| ~/Library/Caches/Homebrew | Homebrew 缓存；使用管理工具的预览能力 |
| ~/Library/Caches/ms-playwright | 浏览器运行文件；其他自动化任务可能仍然依赖它们 |
| ~/.gradle、~/.konan、~/.m2 | JVM、Kotlin 与本地依赖内容；不把整目录当作缓存 |
| ~/.android/avd | 模拟器定义、用户数据、加密相关磁盘和快照；不是普通下载缓存 |
| ~/Library/Developer/Xcode/UserData | 用户设置、断点及签名相关资料；不作为清理候选 |

## 缓存归属

项目中的 iosApp/build/DerivedData 等路径可能是共享增量缓存。先检查项目脚本、活跃进程和实际输出用途；目录名不能证明它可重建。

Xcode 的部分 DerivedData 条目可在 info.plist 中记录 WorkspacePath。以下示例只读取存在的条目，不据此判断目录可删除：

```bash
python3 - <<'PY'
from pathlib import Path
import plistlib

root = Path.home() / "Library/Developer/Xcode/DerivedData"
for file in sorted(root.glob("*/info.plist")):
    try:
        data = plistlib.loads(file.read_bytes())
        print(file.parent, data.get("WorkspacePath", "<not recorded>"))
    except (OSError, ValueError):
        print(file.parent, "<unreadable metadata>")
PY
```

路径不存在也可能是项目移动、外接磁盘未挂载或网络卷不可用。缺少 WorkspacePath 或暂时找不到项目，都不能单独证明缓存是孤儿。
