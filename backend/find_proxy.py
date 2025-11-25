import requests
import socket

# 常见的 VPN 代理端口列表
COMMON_PORTS = [
    7890, 7891, 7897,           # Clash 系列
    1080, 1081, 1082,           # Shadowsocks / V2Ray
    10808, 10809,               # v2rayN
    2080, 2081,                 # NekoBox
    4780, 4781,                 # 其他常见
    9910, 8888, 8889,           # 快橙/其他加速器可能用的
    3128, 8080                  # 通用
]

def check_port(port):
    """检查端口是否开放"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex(('127.0.0.1', port)) == 0:
            return True
    return False

def test_proxy(port):
    """测试该端口能不能上外网"""
    proxies = {
        'http': f'http://127.0.0.1:{port}',
        'https': f'http://127.0.0.1:{port}'
    }
    try:
        print(f"⌛ 发现开放端口 {port}，正在测试连接 YouTube...", end="", flush=True)
        # 强制 3 秒超时
        resp = requests.get("https://www.youtube.com", proxies=proxies, timeout=3)
        if resp.status_code == 200:
            print(" ✅ 通了！")
            return True
        else:
            print(f" ❌ 连上了但状态码不对 ({resp.status_code})")
    except:
        print(" ❌ 无法连接")
    return False

print("🕵️ 开始地毯式扫描...")
found = False

for port in COMMON_PORTS:
    # 先看端口开没开，省时间
    if check_port(port):
        if test_proxy(port):
            print("\n" + "="*40)
            print(f"🎉 找到真凶了！端口号是：{port}")
            print(f"👉 请去 backend/downloader.py 里填入: 'http://127.0.0.1:{port}'")
            print("="*40 + "\n")
            found = True
            break

if not found:
    print("\n🤷‍♂️ 扫描结束，没有发现常见的代理端口。")
    print("结论：你的 VPN 可能使用的是【虚拟网卡模式 (TUN)】，没有开放本地端口。")
    print("建议：")
    print("1. 确保 VPN 开了【全局模式】。")
    print("2. 删除 downloader.py 里的 proxy 配置。")
    print("3. 尝试重启电脑后再次运行。")