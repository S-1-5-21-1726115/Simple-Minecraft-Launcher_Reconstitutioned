"""
使用须知:\r\n
太频繁的"调试"可能会让微软觉得你有毛病然后你就会惨遭紫菜()\r\n
比如:\r\n
出现错误，暂时无法登录。请稍后重试。\r\n
Microsoft 帐户登录服务器检测到身份验证重复尝试次数过多。请稍等片刻，然后重试。\r\n
\r\n
我在调试代码时就被微软紫菜过()\r\n
另外,通常资源文件是一定要重试的,因为太频繁的请求会让服务器宕机\r\n
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
import concurrent.futures,shutil
"""
从此处开始改为from xx import xx的形式
"""
#------校验下载的文件------
from os.path import exists,isfile,isdir,getsize
from hashlib import sha1
#------网络相关,包括异常处理------
from requests.exceptions import *
from requests import get,post,head
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
#------复制文件------
from shutil import copyfile

#------常量区------
strptime=datetime.strptime
strftime=datetime.strftime
AssetsDownloadLink="https://resources.download.minecraft.net/{0}/{1}"
AssetsIndexSavePath="{0}\\assets\\indexes\\{1}.json"
AssetsSavePath="{0}\\assets\\objects\\{1}\\{2}"
LegacySavePath="{0}\\assets\\virtual\\legacy\\{1}"
VersionJSONSavePath="{0}\\versions\\{1}\\{1}.json"
VersionMainFileSavePath="{0}\\versions\\{1}\\{1}.jar"
LibrariesSavePath="{0}\\libraries\\{1}"
Log4j2ConfigSavePath="{0}\\assets\\log_configs\\{1}"

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
            Message_English:str=Response.json()["message"]
            os.system(f"echo {UserCode}|clip")
            print(f"请在 {ExpiresIn} 秒内打开 {VerificationURL} 并输入 {UserCode} 进行身份验证...\r\n\放心,不需要你输入,我们已经帮你复制到剪贴板里了()") #为中国人准备的提示,作者亲自生成()(地理课上讲中文是使用人口最多的语言,外加作者就是中国人,所以中文肯定是要加的)
            print(Message_English) #为外国人准备的提示,微软官方出品(然后地理课上讲英语是适用范围最广的语言,理论上只要有英语提示外国人就能看懂?)
            OpenBrowser(VerificationURL)
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
        except BaseException as e:
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
        Dir:str="\\".join(Path.split("\\")[:-1])
        makedirs(Dir,exist_ok=True)
        with FileIO(Path,mode="w") as IOObject:
            try:
                Data:bytes=get(Url).content
                IOObject.write(Data)
            except BaseException as e:
                print(f"{Path}下载失败!死因:{e}")
                return -1
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
            try:
                Response=get(Url,headers={"Range":Range})
            except Exception as E:
                print(f"{Url}块下载失败!死因:{E}")
            #print(Response.status_code) #调试用语句,206表示部分内容下载成功
            if Response.status_code!=206:
                return -1
            IOObject.write(Response.content)
        return 0
    except:
        return -1

def DownloadFileWithMutilThread(Url:str,Path:str,ThreadCount:int=32)->int:
    """
    多线程下载文件(如果文件大小大于8MB就使用)\r\n
    传入的参数如下:\r\n
    - 文件URL(字符串)\r\n
    - 保存路径(字符串)\r\n
    - 线程数(整数,默认为32)\r\n
    返回错误码(0表示成功,-1表示失败)
    """
    try:
        Dir:str="\\".join(Path.split("\\")[:-1])
        makedirs(Dir,exist_ok=True)
        try:
            FileSize:int=int(head(Url).headers.get("Content-Length",0))
        except Exception as E:
            print(f"{Url}获取文件大小失败!死因:{E}")
            return -1
        if FileSize<=8388608: #如果文件大小小于8MB,就直接下载
            return DownloadFile(Url,Path)
        else:
            #先把所有区块下载到临时目录
            TempDir:str="{}~TMP\\".format(Path)
            makedirs(TempDir,exist_ok=True)
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

            #检查所有线程是否成功
            Result:int=0
            try:
                for _Result in Results:
                    Result+=abs(_Result.result())
                if Result!=0:
                    return -1
            except:
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
    except BaseException as E:
        print(f"{Path}下载失败!死因:{E}")
        return -1

def VerifyFileSHA1(FilePath:str,SHA1:str)->bool:
    """
    校验文件SHA1值是否正确\r\n
    传入的参数如下:\r\n
    - 文件路径(字符串)\r\n
    - SHA1值(字符串)\r\n
    返回布尔值(True表示正确,False表示错误)
    """
    try:
        with FileIO(FilePath,mode="r") as IOObject:
            SHA1Object=sha1()
            while Data:=IOObject.read(1024):
                SHA1Object.update(Data)
            return SHA1Object.hexdigest()==SHA1
    except:
        return False

def VerifyFileSize(FilePath:str,Size:int)->bool:
    """
    校验文件大小是否正确\r\n
    传入的参数如下:\r\n
    - 文件路径(字符串)\r\n
    - 文件大小(整数)\r\n
    返回布尔值(True表示正确,False表示错误)
    """
    try:
        SizeOnDisk:int=getsize(FilePath)
        return SizeOnDisk==Size
    except:
        return False

def DownloadOneFile(File:dict,ThreadCount:int=32):
    """
    下载单个文件(用于创建线程)\r\n
    不用你调用\r\n
    """
    try:
        SavePath:str=File.get("SavePath",False)
        if not SavePath:
            print("\033[31m没保存路径老子不干了啊~\033[0m")
            return ({"SavePath":"-/-","State":"缺少必要信息"},File)
        DownloadLink:str=File.get("DownloadLink",False)
        if not DownloadLink:
            print("\033[31m连链接都没有劳资下个集贸啊?\033[0m")
            return ({"SavePath":SavePath,"State":"缺少必要信息"},File)
        WillVerifySHA1:bool=True
        SHA1:str=File.get("SHA1",False)
        if not SHA1:
            print("\033[32m没SHA1,那就不校验SHA1()\033[0m")
            WillVerifySHA1=False
        WillVerifyFileSize:bool=True
        Size:int=File.get("Size",False)
        if not Size:
            print("\033[32m没文件大小,那就不校验文件大小了\033[0m")
            WillVerifyFileSize=False
        if not (WillVerifySHA1 and WillVerifyFileSize):
            print(f"\033[31m警告:该文件{SavePath}的两种校验方式都无法执行,将不会保证文件的有效性!最好立即检查配置!\033[0m")
        try:
            Result:int=DownloadFileWithMutilThread(Url=DownloadLink,Path=SavePath,ThreadCount=ThreadCount) if not exists(SavePath) else 0
        except BaseException as E: #我们总会有不顺利的时候(试图模仿微软式中文)()(当Mojang服务器被我爬宕机的时候就会抛异常,可能是ProtocolError,也可能是ConnectionError,还可能是SSLError或其他的)
            print(f"\033[31m{SavePath}下载失败!死因:{E}\033[0m")
            return ({"SavePath":SavePath,"State":"失败","MoreInfo":f"下载时出现异常,信息为:{E}"},File)
        
        VerifyFileSHA1Success:bool=True
        VerifyFileSizeSuccess:bool=True
        if Result==0:
            if WillVerifySHA1:
                if VerifyFileSHA1(FilePath=SavePath,SHA1=SHA1):
                    print(f"\033[32m{SavePath}SHA1校验成功!\033[0m")
                else:
                    print(f"\033[31m{SavePath}SHA1校验失败!")
                    VerifyFileSHA1Success=False
            if WillVerifyFileSize:
                if VerifyFileSize(FilePath=SavePath,Size=Size):
                    print(f"\033[32m{SavePath}大小校验成功!\033[0m")
                else:
                    print(f"\033[31m{SavePath}大小校验失败!")
                    VerifyFileSizeSuccess=False
            if VerifyFileSHA1Success and VerifyFileSizeSuccess:
                print(f"\033[32m{SavePath}下载成功!\033[0m")
                return ({"SavePath":SavePath,"State":"成功"},File)
            else:
                print(f"\033[31m{SavePath}校验失败,将会重试...\033[0m")
                print(f"\033[31m已删除无效的{SavePath}")
                remove(SavePath)
                return ({"SavePath":SavePath,"State":"失败","MoreInfo":"校验失败"},File)
        else:
            print(f"\033[31m{SavePath}下载失败,将会重试...\033[0m")
            return ({"SavePath":SavePath,"State":"失败","MoreInfo":"下载时出错"},File)
    except BaseException as E:
        print(f"\033[31m{SavePath}下载失败,死因:{E},将会重试...\033[0m")
        return ({"SavePath":SavePath,"State":"失败","MoreInfo":f"出现异常,信息为:{E}"},File)
    

def DownloadFiles(*args:list[dict]|dict,ThreadCount:int=32,OneFileThreadCount:int=32,RetryCount:int=10,Interval:int=3,**kwargs:list[dict]|dict)->tuple[list[dict],list[dict]]:
    """
    下载一堆文件\r\n
    传入的参数如下:
    - 依托参数,全是列表,列表里面全是字典(当然也可以直接传个字典),字典的键值对如下:
    * DownloadLink:下载链接(字符串)
    * SavePath:保存路径(字符串)
    * SHA1:SHA1值(字符串)(不是必要的,但是建议填上)
    * Size:用于校验的文件大小(整数)(不是必要的,但是建议填上)
    * Size和SHA1可以同时填写,也可以只填一个,也可以都不填,但是都不填的话会显示警告
    - 线程数(整数,默认为32)
    - 重试次数(整数,默认为10)
    - 重试间隔(整数,默认为3秒)\r\n
    返回值是一个列表,列表里面是每个文件状态,是一个元组,里面有两个列表,第一个列表是存储所有下载失败的文件的状态的列表,第二个列表是存储所有下载失败的文件的状态的列表\r\n
    所有列表里面的元素都是字典,字典的键值对如下:\r\n
    * SavePath:保存路径(字符串)
    * State:状态(字符串,成功/失败)
    * MoreInfo:更多信息(字符串,失败时才有这个键,成功时这个键不存在)
    通常来讲,成功的列表里面的字典的State值是"成功",失败的列表里面的字典的State值是"失败"/"缺少信息"\r\n
    如果State值是"缺少信息",那SavePath的值可能是-/-,表示你没有指定保存路径
    """
    Success:list[dict]=[] #下载成功的列表
    WillRetry:list[dict]=[] #下载失败过,即将重试的列表
    Failed:list[dict]=[] #彻底下载失败的列表
    Files:list[dict]=[] #所有待下载的文件列表
    for Arg in args+tuple(kwargs.values()):
        if isinstance(Arg,list):
            for Item in Arg:
                if isinstance(Item,dict):
                    Files.append(Item)
        elif isinstance(Arg,dict):
            Files.append(Arg)
    
    ThreadPool:ThreadPoolExecutor=ThreadPoolExecutor(max_workers=ThreadCount)
    Results:list[concurrent.futures.Future]=[]
    for File in Files:
        Results.append(ThreadPool.submit(DownloadOneFile,File,OneFileThreadCount))
    ThreadPool.shutdown()
    for Result in Results:
        (_Result,FileInfo)=Result.result()
        if _Result["State"]=="成功":
            Success.append(_Result)
        elif _Result["State"]=="失败":
            WillRetry.append(FileInfo)
        else:
            Failed.append(_Result)
    
    for Retry in range(RetryCount):
        if len(WillRetry)==0:
            break
        print(f"\033[32m还有{len(WillRetry)}个文件下载失败,即将在{Interval}秒后重试({Retry+1}/{RetryCount})...\033[0m")
        sleep(Interval) #防止服务器宕机
        ThreadPool:ThreadPoolExecutor=ThreadPoolExecutor(max_workers=ThreadCount)
        Results:list[concurrent.futures.Future]=[]
        print(f"\033[31m还有{len(WillRetry)}个文件下载失败,即将重试({Retry+1}/{RetryCount})...\033[0m")
        for File in WillRetry:
            Results.append(ThreadPool.submit(DownloadOneFile,File,OneFileThreadCount))
        ThreadPool.shutdown()
        for Result in Results:
            (_Result,FileInfo)=Result.result()
            if _Result["State"]=="成功":
                Success.append(_Result)
                WillRetry.remove(FileInfo)
            elif _Result["State"]=="失败":
                if Retry+1==RetryCount:
                    Failed.append(_Result)
                else:
                    continue
            else:
                Failed.append(_Result)
        sleep(1) #留给用户反应时间
    
    SuccessLength:int=len(Success)
    FailedLength:int=len(Failed)
    print("\033[0m\033[32m共有{}个文件下载成功!".format(SuccessLength))
    print("\033[0m\033[32m下载成功的列表:")
    if SuccessLength!=0:
        for SuccessFile in Success:
            print(f"文件路径:{SuccessFile['SavePath']}")
            print(f"状态:{SuccessFile['State']}")
    else:
        print("无")
    
    print("\033[0m\033[31m共有{}个文件下载失败!".format(FailedLength))
    print("\033[0m\033[31m下载失败的列表:")
    if FailedLength!=0:
        for FailedFile in Failed:
            print(f"文件路径:{FailedFile['SavePath']}")
            print(f"状态:{FailedFile['State']}")
            print(f"死因:{FailedFile['MoreInfo']},重试次数超过{RetryCount}次")
    else:
        print("无")
    
    print("\033[0m")
    return (Success,Failed)

def CompleteFiles(Version:str,GameRoot:str,ThreadCount:int=32,OneFileThreadCount:int=32,RetryCount:int=10,Interval:int=3)->int:
    """
    补全文件\r\n
    传入的参数如下:
    - 版本号(字符串)
    - 游戏根目录(字符串)
    - 线程数(整数,默认为32)
    - 单个文件线程数(整数,默认为32)
    - 重试次数(整数,默认为10)\r\n
    返回错误码(0表示成功,-1表示失败)\r\n
    这个补全文件是被我重写过的()
    """
    try:
        VersionJSONFile:TextIOWrapper=TextIOWrapper(FileIO(VersionJSONSavePath.format(GameRoot,Version),mode="r"),encoding="UTF-8")
    except (FileNotFoundError,OSError):
        print(f"\033[31m{Version}的版本文件不存在/拒绝访问!死因:文件不存在或无法打开文件\033[0m")
    try:
        VersionJSON:dict=load(VersionJSONFile)
    except JSONDecodeError as E:
        print(f"\033[31m{Version}的版本文件解析失败!死因:{E}\033[0m")
        return -1
    VersionJSONFile.close()
    del VersionJSONFile #释放内存(IO对象:I'm Free~)
    
    #客户端主文件下载信息
    ClientFileInfo:dict=VersionJSON.get("downloads",{"downloads":{}}).get("client",{})
    if not ClientFileInfo:
        print(f"\033[31m{Version}的版本文件中没有客户端主文件的下载信息\033[0m")
        return -1
    ClientFileSize:int=ClientFileInfo.get("size",0)
    if not bool(ClientFileSize):
        print(f"\033[31m{Version}的版本文件中客户端主文件的大小信息明显不合理!(你家MC的客户端JAR文件0字节?这TM是空文件吧?)\033[0m")
        return -1
    ClientFileSHA1:str=ClientFileInfo.get("sha1","")
    if not ClientFileSHA1:
        print("\033[31m警告:该版本的客户端主文件没有SHA1值,将不会进行校验!最好立即检查配置!(你这个JSON文件是不是有问题啊...一般的版本JSON都是有这玩意的啊?)\033[0m")
    ClientFileDownloadLink:str=ClientFileInfo.get("url",False)
    if not ClientFileDownloadLink:
        print(f"\033[31m{Version}的版本文件中客户端主文件的下载链接信息不完整(这个文件有问题实锤了())\033[0m")
        return -1
    ClientFileSavePath:str=VersionMainFileSavePath.format(GameRoot,Version)
    ClientDownloadInfo:dict={
        "DownloadLink":ClientFileDownloadLink,
        "SavePath":ClientFileSavePath,
        "SHA1":ClientFileSHA1,
        "Size":ClientFileSize
    }
    
    #依赖库文件下载信息
    Libraries:list[dict]=VersionJSON.get("libraries",[])
    if not Libraries:
        print(f"\033[31m{Version}的版本文件中没有依赖库的信息\033[0m")
        return -1
    
    LibrariesDownloadInfo:list[dict]=[]
    for Library in Libraries:
        LibraryDownloadInfo:dict=Library.get("downloads",{"artifact":{}}).get("artifact",{})
        if not LibraryDownloadInfo:
            print("\033[31m警告:该版本的依赖库没有下载信息,将不会进行下载!\033[0m")
            continue
        LibraryDownloadLink:str=LibraryDownloadInfo.get("url","")
        if not LibraryDownloadLink:
            print("\033[31m警告:该依赖库没有下载链接,将不会进行下载!\033[0m")
            continue
        LibraryFileSHA1=LibraryDownloadInfo.get("sha1","")
        if not LibraryFileSHA1:
            print("\033[31m警告:该依赖库没有SHA1值,将不会校验SHA1!\033[0m")
        LibraryFileSize:int=LibraryDownloadInfo.get("size",0)
        if not LibraryFileSize:
            print("\033[31m警告:该依赖库没有文件大小,将不会校验文件大小!(这文件怕是不完整吧?)\033[0m")
        LibraryFilePath:str=LibraryDownloadInfo.get("path","").replace("/","\\")
        if not LibraryFilePath:
            LibraryName:str=Library.get("name","")
            if not LibraryName:
                print("\033[31m警告:该依赖库连名称都没有!无法构建保存路径!\033[0m")
                continue
            else:
                ParsedLibraryName:str=LibraryName.split(":")
                if len(ParsedLibraryName)<3:
                    print("\033[31m警告:该依赖库名称格式不正确!无法构建保存路径!\033[0m")
                    continue
                else:
                    LibraryGroup:str=ParsedLibraryName[0]
                    LibraryArtifact:str=ParsedLibraryName[1]
                    LibraryVersion:str=ParsedLibraryName[2]
                    LibraryFilePath:str="{}\\{}-{}.jar".format(LibraryGroup.replace(".","\\"),LibraryArtifact,LibraryVersion)
        
        FullLibraryFilePath:str=LibrariesSavePath.format(GameRoot,LibraryFilePath)
        LibrariesDownloadInfo.append({
            "DownloadLink":LibraryDownloadLink,
            "SavePath":FullLibraryFilePath,
            "SHA1":LibraryFileSHA1,
            "Size":LibraryFileSize
        })
    
    #Log4j2配置文件下载信息()
    Log4j2ConfigFileInfo:dict=VersionJSON.get("logging",{"logging":{}}).get("client",{"client":""}).get("file",{})
    if not Log4j2ConfigFileInfo:
        print("\033[31m警告:无法获取Log4j2配置文件下载信息!\033[0m")
        return -1
    Log4j2ConfigFileDownloadLink:str=Log4j2ConfigFileInfo.get("url","")
    if not Log4j2ConfigFileDownloadLink:
        print("\033[31m警告:Log4j2配置文件下载链接不完整!\033[0m")
        return -1
    Log4j2ConfigFileName:str=Log4j2ConfigFileInfo.get("id","")
    if not Log4j2ConfigFileName:
        print("\033[31m警告:Log4j2配置文件名称有问题!将使用自定义的名称!\033[0m")
        Log4j2ConfigFileName=f"client-{Version}.xml"
    
    Log4j2ConfigFileSavePath:str=Log4j2ConfigSavePath.format(GameRoot,Log4j2ConfigFileName)
    Log4j2ConfigFileSHA1:str=Log4j2ConfigFileInfo.get("sha1","")
    Log4j2ConfigFileSize:int=Log4j2ConfigFileInfo.get("size",0)
    Log4j2ConfigDownloadInfo:dict={
        "DownloadLink":Log4j2ConfigFileDownloadLink,
        "SavePath":Log4j2ConfigFileSavePath,
        "SHA1":Log4j2ConfigFileSHA1,
        "Size":Log4j2ConfigFileSize
    }
    
    #下载资源索引文件和资源文件
    AssetsIndexInfo:dict=VersionJSON.get("assetIndex",{})
    if not AssetsIndexInfo:
        print("\033[31m警告:无法获取资源索引文件信息!\033[0m")
        return -1
    AssetsIndexDownloadLink:str=AssetsIndexInfo.get("url","")
    if not AssetsIndexDownloadLink:
        print("\033[31m警告:资源索引文件下载链接不完整!\033[0m")
        return -1
    AssetsIndexID:str=AssetsIndexInfo.get("id","")
    if not AssetsIndexID:
        print("\033[31m警告:无法找到资源索引文件ID!\033[0m")
        return -1
    _AssetsIndexSavePath:str=AssetsIndexSavePath.format(GameRoot,AssetsIndexID)
    AssetsIndexSHA1:str=AssetsIndexInfo.get("sha1","")
    if not AssetsIndexSHA1:
        print("\033[31m警告:资源索引文件没有SHA1值,将不会进行校验!\033[0m")
    AssetsIndexSize:int=AssetsIndexInfo.get("size",0)
    if not AssetsIndexSize:
        print("\033[31m警告:资源索引文件大小信息不完整!将不会进行校验!\033[0m")
    AssetsIndexDownloadInfo:dict={
        "DownloadLink":AssetsIndexDownloadLink,
        "SavePath":_AssetsIndexSavePath,
        "SHA1":AssetsIndexSHA1,
        "Size":AssetsIndexSize
    }

    #下载文件
    Success,Failed=DownloadFiles(
        ClientDownloadInfo, #客户端主文件
        LibrariesDownloadInfo, #依赖库文件
        Log4j2ConfigDownloadInfo, #Log4j2配置文件
        AssetsIndexDownloadInfo, #资源索引文件需要比资源文件先下载
        ThreadCount=ThreadCount, #线程数
        OneFileThreadCount=OneFileThreadCount, #单个文件线程数
        RetryCount=RetryCount, #重试次数
        Interval=Interval #重试间隔
    )
    if len(Failed)>0:
        print("\033[31m本次补全文件有部分文件下载失败!\033[0m")
        return -2
    elif Success:
        print("\033[32m本次补全文件全部下载成功!\033[0m")
    else:
        print("\033[31m本次补全文件没有下载任何文件!\033[0m")
        return -3
    
    #下载资源文件
    print("\033[32m别急,还有呢!接下来是为其他资源文件下载的特殊预案...\033[0m")
    print("\033[32m到了此步骤,资源索引文件应该已经下好了,如果出现资源索引文件不存在/无法打开的情况,那就是出现Bug了\033[0m")
    print("\033[32m请向作者反馈该Bug,尽管作者也可能被这个Bug整头大()\033[0m")
    #尽管不太可能(如果解析失败,应该在上一步的校验就报错了;而如果是权限问题/文件不存在,那就应该在下载的时候就报错了)
    try:
        AssetsIndex:list[tuple[str,dict]]=list(load(TextIOWrapper(FileIO(_AssetsIndexSavePath,mode="r"),encoding="UTF-8"))["objects"].items())
    except (FileNotFoundError,OSError,JSONDecodeError,Exception) as E:
        if isinstance(E,JSONDecodeError):
            print(f"\033[31m资源索引文件{_AssetsIndexSavePath}解析失败!死因:{E.__cause__}\033[0m")
        else:
            print(f"\033[31m资源索引文件{_AssetsIndexSavePath}不存在/拒绝访问!死因:文件不存在或无法打开文件\033[0m")
        return -1
    
    AssetsFileDownloadInfo:list[dict]=[]
    for LegacyPath,Asset in AssetsIndex:
        AssetSHA1:str=Asset.get("hash","")
        if not AssetSHA1:
            print(f"\033[31m警告:资源文件{LegacyPath}没有SHA1值,将不会下载!(资源文件的下载链接获取必须依靠SHA1值)\033[0m")
            continue
        AssetSize:int=Asset.get("size",0)
        if not AssetSize:
            print(f"\033[31m警告:资源文件{LegacyPath}没有大小信息,将不会进行校验!\033[0m")
        
        TwoCharsForSHA1:str=AssetSHA1[:2]
        AssetDownloadLink:str=AssetsDownloadLink.format(TwoCharsForSHA1,AssetSHA1)
        AssetSavePath:str=AssetsSavePath.format(GameRoot,TwoCharsForSHA1,AssetSHA1)
        LegacyAssetSavePath:str=LegacySavePath.format(GameRoot,LegacyPath.replace("/","\\"))
        AssetDownloadInfo:dict={
            "DownloadLink":AssetDownloadLink,
            "SavePath":AssetSavePath,
            "SHA1":AssetSHA1,
            "Size":AssetSize,
        }
        LegacyAssetDownloadInfo:dict={
            "DownloadLink":AssetDownloadLink,
            "SavePath":LegacyAssetSavePath,
            "SHA1":AssetSHA1,
            "Size":AssetSize,
        }
        AssetsFileDownloadInfo.append(AssetDownloadInfo)
        AssetsFileDownloadInfo.append(LegacyAssetDownloadInfo)
    
    Success,Failed=DownloadFiles(
        AssetsFileDownloadInfo, #所有资源文件
        ThreadCount=ThreadCount, #线程数
        OneFileThreadCount=OneFileThreadCount, #单个文件线程数
        RetryCount=RetryCount, #重试次数
        Interval=Interval #重试间隔
    )
    if len(Failed)>0:
        print("\033[31m本次资源文件下载有部分文件下载失败!\033[0m")
        return -2
    elif Success:
        print("\033[32m本次资源文件下载全部成功!\033[0m")
        return 0
    else:
        print("\033[31m本次资源文件下载没有下载任何文件!\033[0m")
        return -3

def CheckJava(JavaPath:str="java",JavaVersion:str=22)->bool:
    """
    检查Java版本\r\n
    传入的参数如下:
    - Java路径(字符串,默认为"java")
    - Java版本(字符串,默认为"1.8")\r\n
    """
    try:
        JavaVersionOutput:str=Popen(f"{JavaPath} --version",shell=True,stdout=PIPE,stderr=PIPE).communicate()[0].decode("UTF-8")
    except FileNotFoundError:
        print(f"\033[31mJava路径{JavaPath}不存在!你根本没有安装/在{JavaPath}中安装Java!")
        return False
    JavaVersionOnDisk:float=re.findall("java (.*?) .*",JavaVersionOutput.split("\n")[0],re.S)[0]
    return JavaVersionOnDisk>=JavaVersion

#启动!
def LaunchVersion(Version:str,GameRoot:str,Memory:int=1024,JavaPath:str="java",CustomArgs:str="",
                  AccessTokem:str="",UUID:str="",Username:str="",UserType:str="msa",
                  LauncherName:str="Simple Minecraft Launcher",LauncherVersion:str="0.0.1",
                  CustomWindowTitle:str="",CustomWindowWidth:int=854,CustomWindowHeight:int=480)->int:
    """
    启动游戏\r\n
    传入的参数如下:
    - 版本号(字符串)
    - 游戏根目录(字符串)
    - 内存(整数,默认为1024)
    - Java路径(字符串,默认为"java")
    - 自定义参数(字符串,默认为"")
    \r\n
    - 登录令牌(字符串,默认为"")
    - UUID(字符串,默认为"")
    - 用户名(字符串,默认为"")
    - 用户类型(字符串,默认为"msa")
    \r\n
    - 启动器名称(字符串,默认为"Simple Minecraft Launcher")
    - 启动器版本(字符串,默认为"0.0.1")
    - 自定义窗口标题(字符串,默认为"")
    - 自定义窗口宽度(整数,默认为854)
    - 自定义窗口高度(整数,默认为480)\r\n
    返回错误码(0表示成功,-1表示失败)\r\n
    """
    try:
        VersionJSONFile:TextIOWrapper=TextIOWrapper(FileIO(VersionJSONSavePath.format(GameRoot,Version),mode="r"),encoding="UTF-8")
    except (FileNotFoundError,OSError):
        print(f"\033[31m{Version}的版本文件不存在/拒绝访问!死因:文件不存在或无法打开文件\033[0m")
        return -1
    try:
        VersionInfo:dict=load(VersionJSONFile)
    except JSONDecodeError as E:
        print(f"\033[31m{Version}的版本文件解析失败!死因:{E}\033[0m")
        return -1
    VersionJSONFile.close()
    del VersionJSONFile #释放内存(IO对象:I'm Free~)x2
    ArgumentsInfo:dict=VersionInfo.get("arguments",{})
    if not ArgumentsInfo:
        ArgumentsInfo:str=VersionInfo.get("minecraftArguments","") #版本1.13以后该字段被arguments替代
        if not ArgumentsInfo:
            print("\033[31m该版本没有启动参数!\033[0m") #那就不是我的锅了啊()
            return -1
    
    JVMArgs:list[str|dict]=ArgumentsInfo.get("jvm",[])
    GameArgs:list[str|dict]=ArgumentsInfo.get("game",[])
    if not JVMArgs:
        print("\033[31m该版本没有JVM参数!\033[0m")
        return -1
    if not GameArgs:
        print("\033[31m该版本没有游戏参数!\033[0m")
        return -1
    

#调试用代码
#测试代码
VersionList=GetVersionList()
Version="1.21.4"
GameRoot=".minecraft"
ThreadCount=64
CategoricaledVersions=CategoricalVersions(VersionList)
VersionInfo=FindVersion(Version,CategoricaledVersions)
if not VersionInfo:
    print("没有找到版本信息!")
    exit()
DownloadVersion(VersionInfo,GameRoot)
print(CompleteFiles(Version,GameRoot,ThreadCount,32))