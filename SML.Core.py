"""
使用须知:\r\n
太频繁的"调试"可能会让微软觉得你有毛病然后你就会惨遭紫菜()\r\n
比如:\r\n
出现错误，暂时无法登录。请稍后重试。\r\n
Microsoft 帐户登录服务器检测到身份验证重复尝试次数过多。请稍等片刻，然后重试。\r\n
\r\n
我在调试代码时就被微软紫菜过()\r\n
"""
"""
完全重写
三个库为一组
每一组换个行
仅用于提示使用了哪些库
"""
import platform,requests,json
import subprocess,sys,webbrowser
import random,re,io
import hashlib,datetime,os
import concurrent.futures,math,shutil
"""
从此处开始改为from xx import xx的形式
"""
#------校验下载的文件------
from os.path import exists,isfile,isdir,getsize
from hashlib import sha1
#------网络相关,包括异常处理------
from requests.exceptions import *
from requests import get,post
#------子进程------
from subprocess import Popen,PIPE,STDOUT
#------平台获取------
from platform import system
#------打开浏览器------
from webbrowser import open as OpenBrowser
#------随机数------
from random import randint
#------正则表达式------
from re import search,S
from json import dumps,dump,load
#------文件IO流------
from io import FileIO,BytesIO,TextIOWrapper
#------等待------
from time import sleep,time
#------日期时间------
from datetime import datetime
#------线程------
from concurrent.futures import ThreadPoolExecutor
#------创建/删除目录和删除文件------
from os import makedirs,remove,rmdir
#------绝对值------
from math import fabs
#------复制文件------
from shutil import copyfile

#------常量区------
strptime=datetime.strptime
strftime=datetime.strftime
AssetsDownloadLink="https://resources.download.minecraft.net/{}/{}"
AssetsIndexSavePath="{}\\assets\\indexes\\{}.json"
AssetsSavePath="{}\\assets\\objects\\{}\\{}"
LegacySavePath="{}\\assets\\virtual\\legacy\\{}"

#------备忘录------
#1.获取前两位字符是[:2]
#2.应当在获取资源文件时对资源索引使用.items()方法,因为旧版保存目录的路径就是键名称,而直接使用字典并不支持获取键,而.items()方法可以获取键值对,所以要对加载后的资源索引使用.items()方法(另外,为了方便类型提示,我还会将.items()方法返回的可迭代对象转化为列表)
#3.资源索引文件中的hash是SHA1

"""
呜呜呜面向对象太难了...
"""

#如果面向对象太难了,就先用函数零散的写,然后找到功能相似封装一下

#OK成功封装好了
class AccountManager:
    #第一步骤:OAuth 2.0设备流登录
    @staticmethod
    def GetDeviceCode()->int|tuple[str,str,int]:
        """
        这次我打算换一种方法登录\r\n
        但是这似人GFW就是SB\r\n
        天天屏蔽登录网址\r\n
        把account.live.com给屏蔽掉了\r\n
        太SB了\r\n
        所以你这似人GFW能不能少屏蔽点网址啊!\r\n
        返回值可能是一个整数(出错码),也可能是一个元组(正常情况)\r\n
        第一个是Access Token\r\n
        第二个是Refresh Token\r\n
        第三个是Token过期时间(秒)
        """
        Response:requests.Response=post(
            url="https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode",
            data={
                "client_id":"78914bdb-de6d-4d65-9d88-5f4f9d357db4",
                "scope":"XboxLive.signin offline_access"
            },
            headers={
                "Content-Type":"application/x-www-form-urlencoded"
            },
            params={
                "mtk":"zh-CN"
            }
        )
        if Response.status_code!=200:
            print("这个似人GFW不会把login.microsoftonline.com给屏蔽了吧😰")
            raise ConnectionRefusedError("被GFW紫菜力(悲)")

        else:
            UserCode:str=Response.json()["user_code"]
            DeviceCode:str=Response.json()["device_code"]
            VerificationURL:str=Response.json()["verification_uri"] #通常来讲,网址是https://www.microsoft.com/link，并且会在登录时跳转到account.live.com然后被GFW紫菜
            InterVal:int=Response.json()["interval"]
            ExpiresIn:int=Response.json()["expires_in"]
            print(f"请在 {ExpiresIn} 秒内打开 {VerificationURL} 并输入 {UserCode} 进行身份验证...")
            Count:int=0
            while True:
                Count+=1
                sleep(InterVal)
                Response:requests.Response=post(
                    url="https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={
                        "grant_type":"urn:ietf:params:oauth:grant-type:device_code",
                        "client_id":"78914bdb-de6d-4d65-9d88-5f4f9d357db4",
                        "device_code":DeviceCode,
                    }
                )
                if Response.status_code!=200:
                    if Response.status_code==400 and Response.json()["error"]=="authorization_pending":
                        print(f"等待用户登录...第{Count}次")
                    elif Response.status_code==400 and Response.json()["error"]=="slow_down":
                        continue
                    elif Response.status_code==400 and Response.json()["error"]=="expired_token":
                        print("登录超时")
                        return -1
                    elif Response.status_code==400 and Response.json()["error"]=="authorization_declined":
                        print("用户取消了授权")
                        return -2
                    elif Response.status_code==400 and Response.json()["error"]=="bad_verification_code":
                        print("总感觉获取的东西有问题...")
                        return -3
                else:
                    print("OAuth步骤成功完成")
                    AccessToken:str=Response.json()["access_token"]
                    RefreshToken:str=Response.json()["refresh_token"]
                    ExpiresIn:int=Response.json()["expires_in"]
                    return (AccessToken,RefreshToken,ExpiresIn)

    #刷新令牌
    @staticmethod
    def RefreshToken(RefreshToken:str)->int|tuple[str,str,int]:
        """
        获取新的Token\r\n
        参数是之前获取到的RefreshToken\r\n
        返回值是新的AccessToken\r\n
        通常来讲,你需要等待超时再获取新的Token\r\n
        返回值可能是一个元组,也可能是出错码(通常只可能返回-1)
        """
        Response:requests.Response=post(
            url="https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
            data={
                "client_id":"78914bdb-de6d-4d65-9d88-5f4f9d357db4",
                "refresh_token":RefreshToken,
                "grant_type":"refresh_token",
                "scope":"XboxLive.signin offline_access"
            }
        )
        if Response.status_code!=200:
            if Response.status_code==400 and Response.json()["error"]=="invalid_grant":
                print("RefreshToken无效") #这个倒有可能,比如过期了?(没刷新过AccessToken,应该是每个RefreshEoken只能用一次但不限过期时间?)
                return -1
            elif Response.status_code==400 and Response.json()["error"]=="invalid_request":
                print("请求格式错误") #我不是这样的人啊?
                return -2
            elif Response.status_code==400 and Response.json()["error"]=="unsupported_grant_type":
                print("不支持的grant_type") #怎么可能!
                return -3
        else:
            AccessToken:str=Response.json()["access_token"]
            RefreshToken:str=Response.json()["refresh_token"]
            ExpiresIn:int=Response.json()["expires_in"]
            return (AccessToken,RefreshToken,ExpiresIn)

    #第二步:获取Xbox Live用户信息
    @staticmethod
    def GetXboxLiveUserInfo(AccessToken:str)->tuple[str,str]:
        """
        获取Xbox Live用户信息\r\n
        参数是之前获取到的AccessToken\r\n
        返回值是一个元组\r\n
        元组的第一个元素是Xbox Live 授权Token\r\n
        元组的第二个元素是UHS(你要问这东西是干什么的,我也不知道:)反正获取Minecraft AccessToken时要用到)\r\n
        当然也可能返回错误码:)
        """
        Response:requests.Response=post(
            url="https://user.auth.xboxlive.com/user/authenticate",
            data=dumps({
                "Properties":{
                    "AuthMethod":"RPS",
                    "SiteName":"user.auth.xboxlive.com",
                    "RpsTicket":f"d={AccessToken}"
                },
                "RelyingParty":"http://auth.xboxlive.com",
                "TokenType":"JWT"
            },ensure_ascii=False), #操蛋的之前不小心手贱打成get了!
            headers={
                "Content-Type":"application/json",
                "Accept":"application/json"
            }
        )
        if Response.status_code==400:
            Response:requests.Response=post(
            url="https://user.auth.xboxlive.com/user/authenticate",
            data=dumps({
                    "Properties":{
                        "AuthMethod":"RPS",
                        "SiteName":"user.auth.xboxlive.com",
                        "RpsTicket":AccessToken
                    },
                    "RelyingParty":"http://auth.xboxlive.com",
                    "TokenType":"JWT"
                }),
                headers={
                    "Content-Type":"application/json",
                    "Accept":"application/json"
                },
            ensure_ascii=False) #Wiki上是这么讲的,可以在遇到Bad Request时这么干(叉盒子你就真不能搞个固定的语法吗...)
            if Response.status_code==400:
                print("获取Xbox Live用户信息失败") #那就怪了...
                return -1
        elif Response.status_code!=200:
            print("获取Xbox Live用户信息失败") #遇到其他的我就真不知道咋办了...
            return -2
        else:
            XboxLiveToken:str=Response.json()["Token"]
            UHS:str=Response.json()["DisplayClaims"]["xui"][0]["uhs"]
            return (XboxLiveToken,UHS)

    #第三步:Xsts身份验证
    @staticmethod
    def XstsAuthenticate(XboxLiveToken:str)->int|tuple[str,str]:
        """
        Xsts身份验证\r\n
        参数是之前获取到的XboxLive Token\r\n
        返回值是一个元素\r\n
        第一个是Xsts Token\r\n
        第二个是UHS\r\n
        当然也可能返回错误码.jpg
        """
        Response:requests.Response=post(
            url="https://xsts.auth.xboxlive.com/xsts/authorize",
            data=dumps({
                "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [
                    XboxLiveToken
                ]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
            },ensure_ascii=False),
            headers={
                "Content-Type":"application/json",
                "Accept":"application/json"
            }
        )
        if Response.status_code!=200:
            print("Xsts身份验证失败!") #这个Wiki上没讲可能遇到的错误
            return -1
        else:
            XstsToken:str=Response.json()["Token"]
            UHS:str=Response.json()["DisplayClaims"]["xui"][0]["uhs"]
            return (XstsToken,UHS)

    #第四步:终于开始获取Minecraft AccessToken了...
    @staticmethod
    def GetMinecraftAccessToken(XstsToken:str,UHS:str)->int|tuple[str,int]:
        """" 
        获取Minecraft AccessToken\r\n
        参数是之前获取到的Xsts Token和UHS\r\n
        返回一个元组\r\n
        第一个是Minecraft AccessToken\r\n
        第二个是过期时间(秒)\r\n
        当然也可能又双叒叕返回错误码...
        """
        Response:requests.Response=post(
            url="https://api.minecraftservices.com/authentication/login_with_xbox",
            data=dumps({
                "identityToken":f"XBL3.0 x={UHS};{XstsToken}"
            },ensure_ascii=False)
        )
        if Response.status_code!=200:
            print("获取Minecraft AccessToken失败!") #又是Wiki上没讲的错误...
            return -1
        else:
            MinecraftAccessToken:str=Response.json()["access_token"]
            ExpiresIn:int=Response.json()["expires_in"]
            return (MinecraftAccessToken,ExpiresIn)

    #第五步:获取UUID和账户名,但前提是你必须购买了Minecraft正版账户,否则我是要骂你的oh~
    @staticmethod
    def GetUserInformation(MinecraftAccessToken:str)->int|tuple[str,str]:
        """
        获取UUID和账户名\r\n
        参数是之前获取到的Minecraft AccessToken\r\n
        返回值是一个元组\r\n
        第一个是UUID\r\n
        第二个是账户名\r\n
        当然还是有可能返回错误码()
        """
        Response:requests.Response=get(
            url="https://api.minecraftservices.com/minecraft/profile",
            headers={
                "Authorization":f"Bearer {MinecraftAccessToken}"
            }
        ) #这会儿真是GET了,绝对不会返回405
        if Response.json().get("error",False):
            print("获取账户信息失败!") #绝对是没买正版账户!(反正作者买了,不然作者怎么顺利开发完成的:D)
            return -5
        else:
            UUID:str=Response.json()["id"]
            Username:str=Response.json()["name"]
            return (UUID,Username)
    
    #将前面的步骤整合在一起:
    @staticmethod
    def Login(LastGetRefreshTokenTime:int,LastLoginTime:int,
              LastMinecraftAccessToken:str,LastRefreshToken:str,
              UUID:str,Username:str)->int|tuple[str,str,str,int,float,int,float]:
        """
        你要问为什么一个元组返回这么多...\r\n
        因为返回值是:\r\n
        1.Minecraft AccessToken,当然是必须的,\r\n
        2.UUID,这个启动游戏时当然也是必须的,\r\n
        3.账户名,这个在启动游戏时也会用到,\r\n
        4.RefreshToken的过期时间(90天,每次启动时一旦发现Minecraft AccessToken过期,就自动随着Minecraft AccessToken一起刷新,如果这都过期了...你三个月没登游戏?重登吧~)\r\n
        5.上次获取RefreshToken的时间(秒级时间戳)\r\n
        6.Minecraft AccessToken的过期时间(24小时,一旦检测到过期就会自动刷新(随着刷新的还有RefreshToken的过期时间),当然你不可能玩24小时不中断,所以一般你是不需要重启游戏的)\r\n
        7.上次获取Minecraft AccessToken的时间(秒级时间戳)\r\n
        8.Refresh Token\r\n
        当然也可能返回错误码...\r\n
        """
        #在接下来的步骤之前,先检查一下Minecraft AccessToken是否过期
        NowTime=time()
        if LastLoginTime+86400>=time() and LastMinecraftAccessToken!="": #如果上次登录时间不超过24小时且Minecraft AccessToken不是空的(在另一个函数中新登录的用户这些参数是空的),就直接返回
            print("Minecraft AccessToken有效,直接使用...")
            return (LastMinecraftAccessToken,UUID,Username,(LastGetRefreshTokenTime+7776000)-NowTime,LastGetRefreshTokenTime,(LastLoginTime+86400)-NowTime,LastLoginTime,LastRefreshToken)
        #第一步:OAuth 2.0设备流登录
        if LastLoginTime+7776000<time() or LastRefreshToken=="": #如果上次登录时间超过90天或上一次获取的RefreshToken为空(同样,在另一个函数中新登录的用户这些参数是空的),就重新登录
            print("你已经90天没登录了,请重新登录...") if LastRefreshToken!="" else None
            DeviceCode:int|tuple[str,str,int]=AccountManager.GetDeviceCode()
            if isinstance(DeviceCode,int):
                return DeviceCode
            else:
                AccessToken,RefreshToken,ExpiresIn=DeviceCode
                LastGetRefreshTokenTime=time()
        else: #否则就只是刷新一下
            RefreshToken:int|tuple[str,str,int]=AccountManager.RefreshToken(LastRefreshToken)
            if isinstance(RefreshToken,int):
                return RefreshToken
            else:
                AccessToken,RefreshToken,ExpiresIn=RefreshToken
                LastGetRefreshTokenTime=time()
        
        #第二步:获取Xbox Live用户信息
        XboxLive:int|tuple[str,str]=AccountManager.GetXboxLiveUserInfo(AccessToken)
        if isinstance(XboxLive,int):
            return XboxLive
        else:
            XboxLiveToken,UHS=XboxLive
        
        #第三步:Xsts身份验证
        Xsts:int|tuple[str,str]=AccountManager.XstsAuthenticate(XboxLiveToken)
        if isinstance(Xsts,int):
            return Xsts
        else:
            XstsToken,UHS=Xsts
        
        #第四步:获取Minecraft AccessToken
        TryToGetMinecraftAccessToken:int|tuple[str,int]=AccountManager.GetMinecraftAccessToken(XstsToken,UHS)
        if isinstance(TryToGetMinecraftAccessToken,int):
            return TryToGetMinecraftAccessToken
        else:
            MinecraftAccessToken,MinecraftAccessTokenExpiresIn=TryToGetMinecraftAccessToken
            LastLoginTime=time()
        
        #在进行第五步之前需要先检查UUID和用户名是否为空,因为在别的函数里面新登录的用户UUID和用户名都是空的
        if UUID=="" or Username=="":
            #获取UUID和账户名
            print("获取UUID和账户名...")
            TryToGetUserInformation:int|tuple[str,str]=AccountManager.GetUserInformation(MinecraftAccessToken)
            if isinstance(TryToGetUserInformation,int):
                return TryToGetUserInformation
            else:
                UUID,Username=TryToGetUserInformation
        #如果不为空那就是登录过的账户,直接使用上次的UUID和账户名就好了(这东西每个账户都有一个且永久有效(只要你不注销账户)),不用再获取了
        return (MinecraftAccessToken,UUID,Username,(7776000+LastGetRefreshTokenTime)-NowTime,LastGetRefreshTokenTime,MinecraftAccessTokenExpiresIn,LastLoginTime,RefreshToken)

#启动!

#先获取版本列表
def GetVersionList()->tuple[dict,list[dict]]:
    """
    获取版本列表\r\n
    无参数\r\n
    返回元组\r\n
    具体内容请看:\r\n
    https://zh.minecraft.wiki/w/Tutorial:%E7%BC%96%E5%86%99%E5%90%AF%E5%8A%A8%E5%99%A8/version_manifest.json\r\n
    人话:Minecraft Wiki\r\n
    但进行了一些格式上的修改\r\n
    第一个是最新版本\r\n
    格式差不多是这样的:\r\n
    {\r\n
        "release": "1.21.4",\r\n
        "snapshot": "25w03a"\r\n
    }\r\n
    第二个是所有可用的版本\r\n
    格式差不多是这样的:\r\n
    [\r\n
        {\r\n
            "id": "25w03a",\r\n
            "type": "snapshot",\r\n
            "url": "https://piston-meta.mojang.com/v1/packages/355a00a8bd037d18e80110a4536d0e8b0ea73270/25w03a.json",\r\n
            "time": "2025-01-15T14:39:53+00:00",\r\n
            "releaseTime": "2025-01-15T14:28:04+00:00"\r\n
        },\r\n
        {\r\n
            "id": "25w02a",\r\n
            "type": "snapshot",\r\n
            "url": "https://piston-meta.mojang.com/v1/packages/02a2ae8e2c54cfc39402997bae1bbb2ccc956c84/25w02a.json",\r\n
            "time": "2025-01-08T13:54:13+00:00",\r\n
            "releaseTime": "2025-01-08T13:42:18+00:00"\r\n
        },\r\n
        {\r\n
            "id": "1.21.4",\r\n
            "type": "release",\r\n
            "url": "https://piston-meta.mojang.com/v1/packages/ceac5ecca9292ce18b5bc2565239f4d3a88c5b30/1.21.4.json",\r\n
            "time": "2025-01-15T06:34:26+00:00",\r\n
            "releaseTime": "2024-12-03T10:12:57+00:00"\r\n
        },\r\n
        ......\r\n
    ]\r\n
    提示:这个函数不进行分类,分类函数是另一个
    """
    VersionList:dict=get(
        url="https://piston-meta.mojang.com/mc/game/version_manifest.json",
    ).json()
    LatestVersion:dict=VersionList["latest"]
    AvailableVersions:list[dict]=VersionList["versions"]
    return (LatestVersion,AvailableVersions)

#分类获取的版本
def CategoricalVersions(ParsedVersionList:tuple[dict,list[dict]])->tuple[dict,list[dict],list[dict],list[dict],list[dict]]:
    """
    分类获取的版本\r\n
    参数是GetVersionList的返回值\r\n
    返回值是一个元组\r\n
    第一个是最新版本
    第二个是快照版本\r\n
    第三个是正式版本\r\n
    第四个是远古(Beta)版本\r\n
    第五个是超远古(Alpha以及更早)版本\r\n
    """
    LatestVersion,AvailableVersions=ParsedVersionList
    SnapshotVersions:list[dict]=[]
    ReleaseVersions:list[dict]=[]
    BetaVersions:list[dict]=[]
    AlphaVersions:list[dict]=[]
    for Version in AvailableVersions:
        if Version["type"]=="snapshot":
            SnapshotVersions.append(Version)
        elif Version["type"]=="release":
            ReleaseVersions.append(Version)
        elif Version["type"]=="old_beta":
            BetaVersions.append(Version)
        elif Version["type"]=="old_alpha":
            AlphaVersions.append(Version)
    
    return (LatestVersion,SnapshotVersions,ReleaseVersions,BetaVersions,AlphaVersions)

def FindVersion(VersionName:str,CategorcialVersionList:tuple[dict,list[dict],list[dict],list[dict],list[dict]])->dict|None:
    """
    从已分类的列表里面查找指定的版本\r\n
    参数分别是:\r\n
    - 版本名称\r\n
    - 分类后的版本列表\r\n
    返回值是那个版本的版本文件信息(字典),当然找不到会返回None:)
    """
    LatestVersion,SnapshotVersions,ReleaseVersions,BetaVersions,AlphaVersions=CategorcialVersionList
    for Version in SnapshotVersions+ReleaseVersions+BetaVersions+AlphaVersions:
        if Version["id"]==VersionName:
            return Version
    else:
        return None

def DownloadVersion(Version:dict,DownloadPath:str)->int:
    """
    下载指定版本的文件(其实这个函数只负责下载JSON文件,下载其他的文件由补全函数执行)\r\n
    传入的参数如下:\r\n
    - 版本信息(字典)\r\n
    - 下载路径(字符串)\r\n
    返回错误码(0表示成功,-1表示失败)
    """
    VersionJSONUrl:str=Version["url"]
    #VersionReleaseTime:str=strftime("%Y{}%m{}%d{} %H{}%M{}%S{}",strptime(Version["releaseTime"],"%Y-%m-%dT%H:%M:%S%z")).format("年","月","日","时","分","秒")
    #VersionBuildTime:str=strftime("%Y{}%m{}%d{} %H{}%M{}%S{}",strptime(Version["time"],"%Y-%m-%dT%H:%M:%S%z")).format("年","月","日","时","分","秒")
    VersionName:str=Version["id"]
    VersionType:str=Version["type"]
    VersionFilePath:str="{0}\\Versions\\{1}\\{1}.json".format(DownloadPath,VersionName)
    if (not exists(VersionFilePath)) or isfile(VersionFilePath):
        print("\r\n".join([
            "正在下载版本文件:",
            "版本名称:{0}".format(VersionName),
            "版本类型:{0}".format(VersionType),
        #    "版本发布时间:{0}".format(VersionReleaseTime),
        #    "版本构建时间:{0}".format(VersionBuildTime),
            "将下载到:{0}".format(VersionFilePath)
        ]))
        try:
            if not exists("\\".join(VersionFilePath.split("\\")[:-1])):
                makedirs("\\".join(VersionFilePath.split("\\")[:-1]))
            with TextIOWrapper(FileIO(VersionFilePath,mode="w"),encoding="UTF-8") as IOObject:
                dump(get(VersionJSONUrl).json(),IOObject,indent=4,ensure_ascii=False)
                return 0
        except Exception as e:
            print("下载失败!")
            return -1
    else:
        print("文件已存在,跳过下载...")
        return 0

def DownloadFile(Url:str,Path:str)->int:
    """
    下载单个文件(这里我用了线程,因为同步文件下载太慢了)\r\n
    传入的参数如下:\r\n
    - 文件URL(字符串)\r\n
    - 保存路径(字符串)\r\n
    注意!不检查文件是否存在!如果不存在将会直接覆盖!
    另外,这是下载整个文件!如果需要分块下载请使用DownloadFileWithMutilThread函数!
    """
    try:
        with FileIO(Path,mode="w") as IOObject:
            IOObject.write(get(Url).content)
        return 0
    except:
        return -1

def DownloadBlock(Url:str,TempPath:str,Start:int,End:int)->int:
    """
    下载单个文件块
    参数如下:
    - 文件URL(字符串)
    - 临时保存路径(字符串)
    - 开始位置(整数)
    - 结束位置(整数)
    返回出错码(0表示成功,-1表示失败)
    """
    Range:str="bytes={0}-{1}".format(Start,End)
    try:
        with FileIO(TempPath,mode="w") as IOObject:
            Response=get(Url,headers={"Range":Range})
            print(Response.status_code)
            IOObject.write(Response.content)
        return 0
    except:
        return -1

def DownloadFileWithMutilThread(Url:str,Path:str,ThreadCount:int=32)->int:
    """
    多线程下载文件(如果文件大小大于1MB就使用)\r\n
    传入的参数如下:\r\n
    - 文件URL(字符串)\r\n
    - 保存路径(字符串)\r\n
    - 线程数(整数,默认为32)\r\n
    返回错误码(0表示成功,-1表示失败)
    """
    try:
        FileSize:int=int(get(Url,stream=True).headers.get("Content-Length",0))
        if FileSize<=1048576: #如果文件大小小于1MB,就直接下载
            return DownloadFile(Url,Path)
        else:
            #先把所有区块下载到临时目录
            TempDir:str="{}~TMP\\".format(Path)
            if not exists(TempDir):
                makedirs(TempDir)
            if not exists("\\".join(Path.split("\\")[:-1])):
                makedirs("\\".join(Path.split("\\")[:-1]))
            ChunkSize:int=FileSize//ThreadCount
            ThreadPool=ThreadPoolExecutor(max_workers=ThreadCount)
            Results:list[concurrent.futures.Future]=[]
            for ChunkIndex in range(ThreadCount):
                Start=ChunkIndex*ChunkSize
                End=(Start+ChunkSize-1) if ChunkIndex+1!=ThreadCount else FileSize-1
                TempPath:str="{}{}.tmp".format(TempDir,ChunkIndex)
                Results.append(ThreadPool.submit(DownloadBlock,Url,TempPath,Start,End))
            
            #等待所有线程完成
            ThreadPool.shutdown()

            #检查所有线程是否成功,如果不小心抛出了异常就会被外部的try...except捕获,所以这里不用再try...except了
            Result:int=0
            for _Result in Results:
                Result+=int(fabs(_Result.result()*1.0))
            if Result!=0:
                return -1
            
            #接下来的步骤是合并文件,这一步不需要网络连接,但IO阻塞还是不可避免的()
            with FileIO(Path,mode="w") as IOObject:
                for ChunkIndex in range(ThreadCount):
                    TempPath:str="{}{}.tmp".format(TempDir,ChunkIndex)
                    with FileIO(TempPath,mode="r") as TempIOObject:
                        IOObject.write(TempIOObject.read())
                    remove(TempPath)
                rmdir(TempDir)
        return 0
    except:
        print(f"{Path}下载失败!")
        return -1

def VerifyFile(FilePath:str,SHA1:str)->bool:
    """
    校验文件是否正确\r\n
    通过SHA1校验\r\n
    传入的参数如下:\r\n
    - 文件路径(字符串)\r\n
    - SHA1值(字符串)\r\n
    返回布尔值(True表示正确,False表示错误)
    """
    try:
        with FileIO(FilePath,mode="rb") as IOObject:
            SHA1Object=sha1()
            while Data:=IOObject.read(1024):
                SHA1Object.update(Data)
            return SHA1Object.hexdigest()==SHA1
    except:
        return False

def DownloadLibrary(LibraryInfo:dict,GameRoot:str,ThreadCount:int=32)->int:
    """
    用于开启单个线程的下载库函数\r\n
    参数懂得都懂好吧()
    """
    DownloadInfo:dict=LibraryInfo.get("downloads",{})
    if not DownloadInfo:
        return -1
    Artifact:dict=DownloadInfo.get("artifact",{})
    if not Artifact:
        return -1
    DownloadPath:str=GameRoot+("\\libraries\\"+Artifact.get("path",None)).replace("/","\\")
    if not DownloadPath:
        LibraryName:str=LibraryInfo.get("name")
        if not DownloadPath:
            return -1
        else:
            LibraryNameInfo:list[str]=LibraryName.split(":",1)
            PackageClass:str=LibraryNameInfo[0].replace(".","\\")
            PackageName:str=LibraryNameInfo[1].replace(":","-")
            DownloadPath:str=GameRoot+("\\libraries"+"\\"+PackageName+"\\"+PackageClass+".jar")
    DownloadLink:str=Artifact.get("url",None)
    if not DownloadLink:
        return -1
    SHA1:str=Artifact.get("sha1",None)
    if not SHA1:
        return -1
    FileSize:int=Artifact.get("size",0)
    if not FileSize:
        return -1
    if not exists(DownloadPath):
        print("正在下载文件:{0}".format(DownloadPath))
        DownloadFileWithMutilThread(DownloadLink,DownloadPath,ThreadCount)
        if not (VerifyFile(DownloadPath,SHA1) and getsize(DownloadPath)==FileSize):
            print("文件校验失败!")
            return -2
        else:
            print("下载成功!")
            return 0
    else:
        print("文件已存在,正在校验...")
        if not (VerifyFile(DownloadPath,SHA1) and getsize(DownloadPath)==FileSize):
            print("文件校验失败!")
            print("正在下载文件:{0}".format(DownloadPath))
            DownloadFileWithMutilThread(DownloadLink,DownloadPath)
            if not (VerifyFile(DownloadPath,SHA1) and getsize(DownloadPath)==FileSize):
                print("下载后的文件校验失败!")
                return -2
        else:
            print("文件校验成功!该文件可用!")
            return 0

def DownloadAssetFile(AssetInfo:dict,LegacySavePath:str,GameRoot:str,ThreadCount:int=32)->int:
    """
    单个下载资源文件函数(为了给线程池传参数())\r\n
    参数如下:\r\n
    - 资源信息(字典)\r\n
    - 旧版存档路径(字符串)\r\n
    - 游戏根目录(字符串)\r\n
    - 线程数(整数,默认为32)\r\n
    """
    AssetSHA1:str=AssetInfo.get("hash",None)
    if not AssetSHA1:
        print("没有找到资源文件的SHA1值!")
        return -1
    TwoCharOfSHA1:str=AssetSHA1[:2]
    AssetFileSavePath:str=AssetsSavePath.format(GameRoot,TwoCharOfSHA1,AssetSHA1)
    AssetDownloadLink:str=AssetsDownloadLink.format(TwoCharOfSHA1,AssetSHA1)
    AssetSize:int=AssetInfo.get("size",0)
    if not AssetSize:
        print("没有找到资源文件的大小!")
        return -1
    if not exists(AssetFileSavePath):
        print("正在下载资源文件:{0}".format(AssetFileSavePath))
        DownloadFileWithMutilThread(AssetDownloadLink,AssetFileSavePath,ThreadCount)
        if not (VerifyFile(AssetFileSavePath,AssetSHA1) and getsize(AssetFileSavePath)==AssetSize):
            print("资源文件校验失败!")
            return -1
        else:
            print(f"下载{AssetSHA1}成功!")
            print(f"正在保存至旧版资源路径...")
            if not exists(LegacySavePath):
                copyfile(AssetFileSavePath,LegacySavePath)
            else:
                if VerifyFile(LegacySavePath,AssetSHA1):
                    print(f"旧版资源文件有效,无需复制!")
                else:
                    remove(LegacySavePath)
                    copyfile(AssetFileSavePath,LegacySavePath)
                    print(f"旧版资源文件无效,已复制新资源文件!")

    else:
        print("资源文件已存在,正在校验...")
        if not (VerifyFile(AssetFileSavePath,AssetSHA1) and getsize(AssetFileSavePath)==AssetSize):
            print("资源文件校验失败!")
            print("正在下载资源文件:{0}".format(AssetFileSavePath))
            DownloadFileWithMutilThread(AssetDownloadLink,AssetFileSavePath,ThreadCount)
            if not (VerifyFile(AssetFileSavePath,AssetSHA1) and getsize(AssetFileSavePath)==AssetSize):
                print("下载后的资源文件校验失败!")
                return -1
            else:
                print(f"下载{AssetSHA1}成功!")
                print(f"正在保存至旧版资源路径...")
                if not exists(LegacySavePath):
                    copyfile(AssetFileSavePath,LegacySavePath)
                else:
                    if VerifyFile(LegacySavePath,AssetSHA1):
                        print(f"旧版资源文件有效,无需复制!")
                    else:
                        remove(LegacySavePath)
                        copyfile(AssetFileSavePath,LegacySavePath)
                        print(f"旧版资源文件无效,已复制新资源文件!")
        else:
            print(f"资源文件{AssetSHA1}校验成功!该文件可用!")
            print(f"正在保存至旧版资源路径...")
            if not exists(LegacySavePath):
                copyfile(AssetFileSavePath,LegacySavePath)
            else:
                if VerifyFile(LegacySavePath,AssetSHA1):
                    print(f"旧版资源文件有效,无需复制!")
                else:
                    remove(LegacySavePath)
                    copyfile(AssetFileSavePath,LegacySavePath)
                    print(f"旧版资源文件无效,已复制新资源文件!")
    return 0

def DownloadAssetsFile(AssetsIndex:list[tuple[str,dict]],GameRoot:str,ThreadCount:int=32)->int:
    """
    下载资源文件,通常在补全文件的时候使用\r\n
    参数如下:\r\n
    - 资源索引(列表,元组的列表)\r\n
    - 游戏根目录(字符串)\r\n
    - 线程数(整数,默认为32)\r\n
    """
    Results:list=[]
    ThreadPool=ThreadPoolExecutor(max_workers=ThreadCount)
    for LegacySavePath,AssetInfo in AssetsIndex:
        Results.append(ThreadPool.submit(DownloadAssetFile,AssetInfo,LegacySavePath,GameRoot,ThreadCount))
    
    #等待所有线程完成
    ThreadPool.shutdown()
    #检查所有线程是否成功,这次外部没有try...except,所以这里需要防止不小心抛出异常
    try:
        Result:int=0
        for _Result in Results:
            Result+=int(fabs(_Result.result()*1.0))
        if Result!=0:
            return -1
    except:
        return -1
    return 0

def CompleteFiles(Version:str,GameRoot:str,ThreadCount:int=32,OneFileThreadCount:int=32)->int:
    """
    补全文件(通常在启动游戏之前)\r\n
    传入的参数如下:\r\n
    - 版本名称(字符串),例如"25w04a"\r\n
    - 下载路径(字符串)(通常是游戏目录,一般是.minecraft,当然你也可以自定义)\r\n
    - 线程数(整数,默认为32)\r\n
    - 单个文件下载线程数(整数,默认为32)\r\n
    返回错误码(0表示成功,-1表示失败)
    """
    #基础信息

    VersionFilePath:TextIOWrapper=TextIOWrapper(FileIO("{0}\\Versions\\{1}\\{1}.json".format(GameRoot,Version)),encoding="UTF-8")
    VersionInfo:dict=load(VersionFilePath)
    AssetsIndex:dict=VersionInfo.get("assetIndex",{})
    if not AssetsIndex:
        print("没有找到AssetsIndex!")
        return -1
    Client_or_Server_Download:dict=VersionInfo.get("downloads",{})
    if not Client_or_Server_Download:
        print("没有找到下载信息!")
        return -1
    Libraries:list[dict]=VersionInfo.get("libraries",[])
    if not Libraries:
        print("没有找到库信息!")
        return -1
    
    #下载库文件
    Results:list[concurrent.futures.Future]=[]
    ThreadPool=ThreadPoolExecutor(max_workers=ThreadCount)
    for LibraryInfo in Libraries:
        Results.append(ThreadPool.submit(DownloadLibrary,LibraryInfo,GameRoot,OneFileThreadCount))
    #等待所有线程完成
    ThreadPool.shutdown()
    #检查所有线程是否成功,这次外部没有try...except,所以这里需要防止不小心抛出异常
    try:
        Result:int=0
        for _Result in Results:
            Result+=int(fabs(_Result.result()*1.0))
        if Result!=0:
            return -1
    except:
        return -1
    
    #下载资源索引文件
    AssetsIndexDownloadLink:str=Client_or_Server_Download.get("url",None)
    if not AssetsIndexDownloadLink:
        print("没有找到AssetsIndex下载链接!")
        return -1
    AssetsIndexSHA1:str=AssetsIndex.get("sha1",None)
    if not AssetsIndexSHA1:
        print("没有找到AssetsIndex的SHA1值!")
        return -1
    AssetsIndexSize:int=Client_or_Server_Download.get("size",0)
    if not AssetsIndexSize:
        print("没有找到AssetsIndex的大小!")
        return -1
    AssetsIndexID:str=AssetsIndex.get("id",None)
    AssetsIndexPath:str=AssetsIndexSavePath.format(GameRoot,AssetsIndexID)
    if not exists(AssetsIndexPath):
        print("正在下载AssetsIndex文件:{0}".format(AssetsIndexPath))
        DownloadFileWithMutilThread(AssetsIndexDownloadLink,AssetsIndexPath,OneFileThreadCount)
        if not (VerifyFile(AssetsIndexPath,AssetsIndexSHA1) and getsize(AssetsIndexPath)==AssetsIndexSize):
            print("AssetsIndex文件校验失败!")
            return -2
        else:
            print("下载成功!")
    else:
        print("AssetsIndex文件已存在,正在校验...")
        if not (VerifyFile(AssetsIndexPath,AssetsIndexSHA1) and getsize(AssetsIndexPath)==AssetsIndexSize):
            print("AssetsIndex文件校验失败!")
            print("正在下载AssetsIndex文件:{0}".format(AssetsIndexPath))
            DownloadFileWithMutilThread(AssetsIndexDownloadLink,AssetsIndexPath,OneFileThreadCount)
            if not (VerifyFile(AssetsIndexPath,AssetsIndexSHA1) and getsize(AssetsIndexPath)==AssetsIndexSize):
                print("下载后的AssetsIndex文件校验失败!")
                return -2
        else:
            print("AssetsIndex文件校验成功!该文件可用!")
    
    #下载资源文件
    AssetsInfo:dict=load(AssetsIndexPath)
    AssetsIndex:list[tuple[str,dict]]=list(AssetsInfo.items())
    Results:int=DownloadAssetsFile(AssetsIndex,GameRoot,OneFileThreadCount)
    if Results!=0:
        return -3

    #下载客户端文件(倒数第二步)
    ClientDownloadInfo:dict=Client_or_Server_Download.get("client",None)
    if not ClientDownloadInfo:
        print("没有找到客户端下载信息!")
        return -1
    ClientDownloadLink:dict=ClientDownloadInfo.get("url",None)
    if not ClientDownloadLink:
        print("没有找到客户端下载链接!")
        return -1
    ClientSHA1:str=ClientDownloadInfo.get("sha1",None)
    if not ClientSHA1:
        print("没有找到客户端的SHA1值!")
        return -1
    ClientSize:int=ClientDownloadInfo.get("size",0)
    if ClientSize<=0:
        print("没有找到客户端的大小!")
        return -1
    ClientPath:str="{0}\\Versions\\{1}\\{1}.jar".format(GameRoot,Version)
    if not exists(ClientPath):
        print("正在下载客户端文件:{0}".format(ClientPath))
        DownloadFileWithMutilThread(ClientDownloadLink,ClientPath,OneFileThreadCount)
        if not (VerifyFile(ClientPath,ClientSHA1) and getsize(ClientPath)==ClientSize):
            print("客户端文件校验失败!")
            return -4
        else:
            print("下载成功!")
    else:
        print("客户端文件已存在,正在校验...")
        if not (VerifyFile(ClientPath,ClientSHA1) and getsize(ClientPath)==ClientSize):
            print("客户端文件校验失败!")
            print("正在下载客户端文件:{0}".format(ClientPath))
            DownloadFileWithMutilThread(ClientDownloadLink,ClientPath,OneFileThreadCount)
            if not (VerifyFile(ClientPath,ClientSHA1) and getsize(ClientPath)==ClientSize):
                print("下载后的客户端文件校验失败!")
                return -4
        else:
            print("客户端文件校验成功!该文件可用!")
    
    #下载Log4j配置文件(最后一步)
    Log4jInfo:dict=VersionInfo.get("logging",{})
    if not Log4jInfo:
        print("没有找到Log4j配置文件信息!")
        return -1
    Log4jClientInfo:dict=Log4jInfo.get("client",{})
    if not Log4jClientInfo:
        print("没有在Log4j配置文件中找到客户端配置信息!")
        return -1
    Log4jDownloadInfo:dict=Log4jClientInfo.get("file",{})
    if not Log4jDownloadInfo:
        print("没有找到Log4j配置文件的下载信息!")
        return -1
    Log4jDownloadLink:str=Log4jDownloadInfo.get("url",None)
    if not Log4jDownloadLink:
        print("没有找到Log4j配置文件的下载链接!")
        return -1
    Log4jSHA1:str=Log4jDownloadInfo.get("sha1",None)
    if not Log4jSHA1:
        print("没有找到Log4j配置文件的SHA1值!")
        return -1
    Log4jProfileSize:int=Log4jDownloadInfo.get("size",0)
    if Log4jProfileSize<=0:
        print("没有找到Log4j配置文件的大小!")
        return -1
    Log4jProfileName:str=Log4jDownloadInfo.get("id",None)
    if not Log4jProfileName:
        Log4jProfileName="client-1.21.2.xml" #←默认的配置文件名,另外,最好使用高版本的Log4j配置文件,因为低版本的配置文件存在严重的漏洞(CVE-2021-44228),会导致电脑被别人报废
                                             #↑具体信息请看:https://zh.minecraft.wiki/w/Tutorial:%E4%BF%AE%E5%A4%8DApache_Log4j2%E6%BC%8F%E6%B4%9E
                                             #↑1.18.1-rc3及以上版本就没这个漏洞了
                                             #↑1.18.1比1.18除了修复这个漏洞以外没有什么区别,甚至1.18.1兼容1.18的服务端和存档,所以想玩1.18的建议使用1.18.1或1.18.2
                                             #↑1.17请使用-Dlog4j2.formatMsgNoLookups=true参数来修复
                                             #↑1.12至1.16.5除了上述参数以外还要先下载https://piston-data.mojang.com/v1/objects/02937d122c86ce73319ef9975b58896fc1b491d1/log4j2_112-116.xml
                                             #↑然后放到任意目录下并指定-Dlog4j.configurationFile=<你的存放配置文件的路径,应该是相对路径>(这文件名一看就是Mojang(划掉)ojng临时修复的)
                                             #↑1.7至1.11.2请下载https://piston-data.mojang.com/v1/objects/4bb89a97a66f350bc9f73b3ca8509632682aea2e/log4j2_17-111.xml
                                             #↑并同样指定-Dlog4j.configurationFile=<你的存放配置文件的路径,应该是相对路径>
                                             #↑1.6.4及以下版本没有这个漏洞,不用担心
    Log4jProfilePath:str="{0}\\assets\\log_configs\\{1}".format(GameRoot,Log4jProfileName) #这里的路径可以随意指定,但最好能让别人一看就知道这玩意是干什么的,比如官方启动器的.minecraft/assets/log_configs就很直观
    if not exists(Log4jProfilePath):
        print("正在下载Log4j配置文件:{0}".format(Log4jProfilePath))
        DownloadFileWithMutilThread(Log4jDownloadLink,Log4jProfilePath,OneFileThreadCount)
        if not (VerifyFile(Log4jProfilePath,Log4jSHA1) and getsize(Log4jProfilePath)==Log4jProfileSize):
            print("Log4j配置文件校验失败!")
            return -5
        else:
            print("下载成功!")
    else:
        print("Log4j配置文件已存在,正在校验...")
        if not (VerifyFile(Log4jProfilePath,Log4jSHA1) and getsize(Log4jProfilePath)==Log4jProfileSize):
            print("Log4j配置文件校验失败!")
            print("正在下载Log4j配置文件:{0}".format(Log4jProfilePath))
            DownloadFileWithMutilThread(Log4jDownloadLink,Log4jProfilePath,OneFileThreadCount)
            if not (VerifyFile(Log4jProfilePath,Log4jSHA1) and getsize(Log4jProfilePath)==Log4jProfileSize):
                print("下载后的Log4j配置文件校验失败!")
                return -5
        else:
            print("Log4j配置文件校验成功!该文件可用!")
    
    print("所有文件补全成功!")
    return 0

#不写了该调试了
#测试代码
VersionList=GetVersionList()
Version="1.21.4"
GameRoot=".minecraft"
ThreadCount=1
CategoricaledVersions=CategoricalVersions(VersionList)
VersionInfo=FindVersion(Version,CategoricaledVersions)
if not VersionInfo:
    print("没有找到版本信息!")
    exit()
DownloadVersion(VersionInfo,GameRoot)
CompleteFiles(Version,GameRoot,ThreadCount,32)