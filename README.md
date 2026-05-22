# 阿里云 OSS 文件管理工具

项目地址：https://github.com/koi-pig/aly-oss-gui

这是一个 PySide6 桌面工具，可以选择 Bucket、上传文件、显示上传进度、按原 OSS 链接覆盖文件、查看文件列表、复制链接、删除文件。

## 打包 exe

```powershell
cd d:/Desktop/rrb/doc/docs/aly_oss_gui
powershell -ExecutionPolicy Bypass -File ./build_exe.ps1
```

每次打包会删除 `dist` 目录里的旧 exe，只保留最终版 `dist/AlyOssTool.exe`。

## 生成配置文件

第一次启动时，如果软件同目录没有 `config.local.json`，程序会自动弹出“OSS 配置”窗口。填写后点击保存，会自动生成配置文件。

## 配置字段

```json
{
  "access_key_id": "你的 AccessKey ID",
  "access_key_secret": "你的 AccessKey Secret",
  "bucket": "你自己的 Bucket 名称",
  "endpoint": "http://oss-cn-hangzhou.aliyuncs.com",
  "view_endpoint": "https://%s.oss-cn-hangzhou.aliyuncs.com/%s",
  "signed_url_expire_seconds": 315360000,
  "page_size": 10,
  "multipart_threshold_mb": 10,
  "multipart_part_size_mb": 8,
  "multipart_threads": 16
}
```

`bucket` 必须改成你自己的 OSS Bucket 名称。

`endpoint` 要写 Bucket 对应地域，例如：

```text
oss-cn-hangzhou -> http://oss-cn-hangzhou.aliyuncs.com
oss-cn-shanghai -> http://oss-cn-shanghai.aliyuncs.com
oss-cn-beijing  -> http://oss-cn-beijing.aliyuncs.com
```

大文件上传会自动启用分片并发上传：

- `multipart_threshold_mb`：文件大于等于多少 MB 启用分片上传，默认 10。
- `multipart_part_size_mb`：每个分片大小，默认 8。
- `multipart_threads`：并发上传线程数，默认 16，不稳定时改回 8。
