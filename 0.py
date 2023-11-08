import os
import re
import sys
import datetime
from time import sleep
import hashlib
import win32gui
import win32con
import win32api
import win32com.client
import requests

# win环境下的快速开发脚本

# 检查localConfig.py是否存在
if not os.path.exists("localConfig.py"):
    print("localConfig.py不存在，已自动创建，请配置路径")
    with open("localConfig.py", "w", encoding="utf-8") as f:
        f.write(
            "# main工程路径: \n"
            + "# 例: mainProjectPath = r"
            + r'"C:\Users\DazeCake\Documents\Tools\懒人精灵3.8.3\script\main"'
            + "\n"
            + 'mainProjectPath = r""\n'
            + "# 打包的main.lr路径: \n"
            + "# 例: lrPath = r"
            + r'"C:\Users\DazeCake\Documents\Tools\懒人精灵3.8.3\out\main.lr"'
            + "\n"
            + 'lrPath = r""\n\n'
            + "# 热更新token: \n"
            + 'token = ""\n'
        )
        exit()

# 检查localConfig.py是否配置
import localConfig as lc

if lc.mainProjectPath == "" or lc.lrPath == "":
    print("localConfig.py未配置，请配置路径")
    exit()
else:
    path = lc.mainProjectPath
    pkgPath = lc.lrPath


class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""

    def __init__(self):
        """Constructor"""
        self._handle = None

    def find_window(self, class_name, window_name=None):
        """基于类名来查找窗口"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, class_name_wildcard_list):
        """传递给win32gui.EnumWindows()，检查所有打开的顶级窗口"""
        class_name, wildcard = class_name_wildcard_list
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, class_name, wildcard):
        """根据类名，查找一个顶级窗口，确保其类名相符，且标题可以用正则表达式匹配对应的通配符"""
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, [class_name, wildcard])
        return self._handle

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)

    def get_hwnd(self):
        """return hwnd for further use"""
        return self._handle


def run(now=True):
    """自动运行调试 需提前打开任意lua文件"""
    myWindowMgr = WindowMgr()
    hwnd = myWindowMgr.find_window_wildcard(None, ".*?懒人精灵 - .*?")
    if hwnd != None:
        win32gui.BringWindowToTop(hwnd)
        # 先发送一个alt事件，否则会报错导致后面的设置无效：pywintypes.error: (0, 'SetForegroundWindow', 'No error message is available')
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys("%")
        # 设置为当前活动窗口
        win32gui.SetForegroundWindow(hwnd)
        # 最大化窗口
        # win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        # F6
        win32api.keybd_event(117, win32api.MapVirtualKey(117, 0), 0, 0)
        win32api.keybd_event(
            117, win32api.MapVirtualKey(117, 0), win32con.KEYEVENTF_KEYUP, 0
        )
        sleep(0.1)
        # F5
        if now:
            win32api.keybd_event(116, win32api.MapVirtualKey(116, 0), 0, 0)
            win32api.keybd_event(
                116, win32api.MapVirtualKey(116, 0), win32con.KEYEVENTF_KEYUP, 0
            )


def save():
    """保存到懒人精灵工程文件夹"""

    # 获取当前目录下所有的.lua文件
    lua_files = [f for f in os.listdir(".") if f.endswith(".lua")]
    for lua_file in lua_files:
        # 把lua_file以utf-8的格式打开，然后以GB18030的格式写入到"D:\ArkLights\main\脚本"目录下
        with open(lua_file, "r", encoding="utf-8") as f:
            with open(
                os.path.join(path, "脚本", lua_file), "w", encoding="GB18030"
            ) as f1:
                f1.write(f.read())

    # 获取当前目录下所有的.ui文件
    ui_files = [f for f in os.listdir(".") if f.endswith(".ui")]
    for ui_file in ui_files:
        # 把ui_file以utf-8的格式打开，然后以GB18030的格式写入到path+界面目录下
        with open(ui_file, "r", encoding="utf-8") as f:
            with open(os.path.join(path, "界面", ui_file), "w", encoding="GB18030") as f1:
                f1.write(f.read())

    print("保存完成")


def saverun():
    """保存并运行"""
    save()
    run()


def release(type):
    if type == "RELEASE":
        save()
        run(False)

        newLrMD5 = input("请输入md5值: ")
        # 输出pkgPath的文件的md5
        md5 = hashlib.md5()
        with open(pkgPath, "rb") as f:
            md5.update(f.read())
        md5Text = md5.hexdigest()

        # 判断输入值是否与md5Text相等
        if newLrMD5 == md5Text:
            print("md5值正确")
            # 上传
            upload(md5Text, type, "false")
        else:
            print("md5值错误")
    elif type == "SKILL":
        upload("", type, "false")


def upload(md5, type, force):
    token = lc.token
    if token == "":
        print("token未配置，请配置token")
        exit()
    upFile = ""
    if type == "RELEASE":
        upFile = pkgPath
    elif type == "SKILL":
        upFile = r"res\skill.zip"
    md5 = hashlib.md5()
    with open(upFile, "rb") as f:
        md5.update(f.read())
    md5Text = md5.hexdigest()
    url = (
        "http://ark.aegirtech.com:8080/uploadHotUpdatePackage?token="
        + token
        + "&md5="
        + md5Text
        + "&type="
        + type
        + "&force="
        + force
    )

    fileName = ""
    if type == "RELEASE":
        fileName = "script.lr"
    elif type == "SKILL":
        fileName = "skill.zip"

    payload = {}
    files = [("fille", (fileName, open(upFile, "rb"), "application/octet-stream"))]
    headers = {"User-Agent": "Apifox/1.0.0 (https://apifox.com)"}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    print(response.json().get("msg"))


def statistician():
    token = lc.token
    if token == "":
        print("token未配置，请配置token")
        exit()
    url = "http://ark.aegirtech.com:8080/getStatistician?token=" + token
    response = requests.request("GET", url)
    info = response.json()["data"]
    print("============统计信息============")
    print("24h下载量: \t" + str(info["downloadCount"]))
    print("终端数量:  \t" + str(info["alCount"]))
    print("账号数量:  \t" + str(info["accountCount"]))
    print("活跃终端数量:  \t" + str(info["activeAlCount"]))
    print("活跃账号数量:  \t" + str(info["activeAccountCount"]))


if __name__ == "__main__":
    try:
        arg = sys.argv[1]
        if arg == "run":
            run()
        elif arg == "save":
            save(False)
        elif arg == "saverun":
            saverun()
        elif arg == "r":
            release("RELEASE")
        elif arg == "rs":
            release("SKILL")
        elif arg == "s":
            statistician()

    except Exception as e:
        print("缺少正确参数或没有启用管理员权限")
        print(
            """
run: 运行
save: 保存
saverun: 保存并运行
r: 发布脚本
rs: 发布技能图标
"""
        )
