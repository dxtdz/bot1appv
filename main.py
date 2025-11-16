import discord
from discord.ext import commands
import asyncio
import os
import re
import time
import json
import base64
import random
import requests
from discord import ButtonStyle
from discord.ui import Button, View
from datetime import datetime
from typing import Dict, Any
from keep_alive import keep_alive

# Nhập dữ liệu khi khởi chạy
TOKEN = input("\033[32m Vui Lòng Nhập Token Bot:\033[37m ")
IDADMIN_GOC = int(input("\033[32m Vui Lòng Nhập Id Admin Gốc:\033[37m "))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

keep_alive()


@bot.event
async def on_ready():
    print(f'\033[35m{bot.user} đã kết nối thành công')


# RAM lưu trạng thái
admins = [IDADMIN_GOC]
saved_files = {}
running_tasks = {}
active_tokens = {}
discord_threads = {}
discord_states = {}
task_info = {}

# ========== UTILITY FUNCTIONS ==========


def get_uid(cookie):
    try:
        return re.search('c_user=(\\d+)', cookie).group(1)
    except:
        return '0'


def get_fb_dtsg_jazoest(cookie, target_id):
    try:
        response = requests.get(
            f'https://mbasic.facebook.com/privacy/touch/block/confirm/?bid={target_id}&ret_cancel&source=profile',
            headers={
                'cookie': cookie,
                'user-agent': 'Mozilla/5.0'
            })
        fb_dtsg = re.search('name="fb_dtsg" value="([^"]+)"',
                            response.text).group(1)
        jazoest = re.search('name="jazoest" value="([^"]+)"',
                            response.text).group(1)
        return fb_dtsg, jazoest
    except:
        return None, None


def send_message(idcanspam,
                 fb_dtsg,
                 jazoest,
                 cookie,
                 message_body,
                 tag_uid=None,
                 tag_name=None):
    try:
        uid = get_uid(cookie)
        timestamp = int(time.time() * 1000)

        data = {
            'thread_fbid': idcanspam,
            'action_type': 'ma-type:user-generated-message',
            'body': message_body,
            'client': 'mercury',
            'author': f'fbid:{uid}',
            'timestamp': timestamp,
            'source': 'source:chat:web',
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'ephemeral_ttl_mode': '',
            '__user': uid,
            '__a': '1',
            '__req': '1b',
            '__rev': '1015919737',
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest
        }

        if tag_uid and tag_name:
            tag_text = f"@{tag_name}"
            tag_position = message_body.find(tag_text)
            if tag_position != -1:
                data['profile_xmd[0][offset]'] = str(tag_position)
                data['profile_xmd[0][length]'] = str(len(tag_text))
                data['profile_xmd[0][id]'] = tag_uid
                data['profile_xmd[0][type]'] = 'p'

        headers = {
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.facebook.com',
            'Referer': f'https://www.facebook.com/messages/t/{idcanspam}'
        }

        response = requests.post('https://www.facebook.com/messaging/send/',
                                 data=data,
                                 headers=headers)
        return response.status_code == 200
    except:
        return False


def get_guid():
    section_length = int(time.time() * 1000)

    def replace_func(c):
        nonlocal section_length
        r = (section_length + random.randint(0, 15)) % 16
        section_length //= 16
        return hex(r if c == "x" else (r & 7) | 8)[2:]

    return "".join(
        replace_func(c) if c in "xy" else c
        for c in "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx")


def normalize_cookie(cookie, domain='www.facebook.com'):
    headers = {
        'Cookie':
        cookie,
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(f'https://{domain}/',
                                headers=headers,
                                timeout=10)
        if response.status_code == 200:
            set_cookie = response.headers.get('Set-Cookie', '')
            new_tokens = re.findall(r'([a-zA-Z0-9_-]+)=[^;]+', set_cookie)
            cookie_dict = dict(re.findall(r'([a-zA-Z0-9_-]+)=([^;]+)', cookie))
            for token in new_tokens:
                if token not in cookie_dict:
                    cookie_dict[token] = ''
            return ';'.join(f'{k}={v}' for k, v in cookie_dict.items() if v)
    except:
        pass
    return cookie


def get_uid_fbdtsg(ck):
    try:
        headers = {
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':
            'gzip, deflate',
            'Accept-Language':
            'en-US,en;q=0.9,vi;q=0.8',
            'Connection':
            'keep-alive',
            'Cookie':
            ck,
            'Host':
            'www.facebook.com',
            'Sec-Fetch-Dest':
            'document',
            'Sec-Fetch-Mode':
            'navigate',
            'Sec-Fetch-Site':
            'none',
            'Sec-Fetch-User':
            '?1',
            'Upgrade-Insecure-Requests':
            '1',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }

        try:
            response = requests.get('https://www.facebook.com/',
                                    headers=headers)

            if response.status_code != 200:
                print(f"Status Code >> {response.status_code}")
                return None, None, None, None, None, None

            html_content = response.text

            user_id = None
            fb_dtsg = None
            jazoest = None

            script_tags = re.findall(
                r'<script id="__eqmc" type="application/json[^>]*>(.*?)</script>',
                html_content)
            for script in script_tags:
                try:
                    json_data = json.loads(script)
                    if 'u' in json_data:
                        user_param = re.search(r'__user=(\d+)', json_data['u'])
                        if user_param:
                            user_id = user_param.group(1)
                            break
                except:
                    continue

            fb_dtsg_match = re.search(r'"f":"([^"]+)"', html_content)
            if fb_dtsg_match:
                fb_dtsg = fb_dtsg_match.group(1)

            jazoest_match = re.search(r'jazoest=(\d+)', html_content)
            if jazoest_match:
                jazoest = jazoest_match.group(1)

            revision_match = re.search(
                r'"server_revision":(\d+),"client_revision":(\d+)',
                html_content)
            rev = revision_match.group(1) if revision_match else ""

            a_match = re.search(r'__a=(\d+)', html_content)
            a = a_match.group(1) if a_match else "1"

            req = "1b"

            return user_id, fb_dtsg, rev, req, a, jazoest

        except requests.exceptions.RequestException as e:
            print(f"Lỗi Kết Nối Khi Lấy UID/FB_DTSG: {e}")
            return get_uid_fbdtsg(ck)

    except Exception as e:
        print(f"Lỗi: {e}")
        return None, None, None, None, None, None


def get_info(uid: str, cookie: str, fb_dtsg: str, a: str, req: str,
             rev: str) -> Dict[str, Any]:
    try:
        form = {
            "ids[0]": uid,
            "fb_dtsg": fb_dtsg,
            "__a": a,
            "__req": req,
            "__rev": rev
        }

        headers = {
            'Accept':
            '*/*',
            'Accept-Language':
            'en-US,en;q=0.9,vi;q=0.8',
            'Connection':
            'keep-alive',
            'Content-Type':
            'application/x-www-form-urlencoded',
            'Cookie':
            cookie,
            'Origin':
            'https://www.facebook.com',
            'Referer':
            'https://www.facebook.com/',
            'Sec-Fetch-Dest':
            'empty',
            'Sec-Fetch-Mode':
            'cors',
            'Sec-Fetch-Site':
            'same-origin',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }

        response = requests.post("https://www.facebook.com/chat/user_info/",
                                 headers=headers,
                                 data=form)

        if response.status_code != 200:
            return {"error": f"Lỗi Kết Nối: {response.status_code}"}

        try:
            text_response = response.text
            if text_response.startswith("for (;;);"):
                text_response = text_response[9:]

            res_data = json.loads(text_response)

            if "error" in res_data:
                return {"error": res_data.get("error")}

            if "payload" in res_data and "profiles" in res_data["payload"]:
                return format_data(res_data["payload"]["profiles"])
            else:
                return {"error": f"Không Tìm Thấy Thông Tin Của {uid}"}

        except json.JSONDecodeError:
            return {"error": "Lỗi Khi Phân Tích JSON"}

    except Exception as e:
        print(f"Lỗi Khi Get Info: {e}")
        return {"error": str(e)}


def format_data(profiles):
    if not profiles:
        return {"error": "Không Có Data"}

    first_profile_id = next(iter(profiles))
    profile = profiles[first_profile_id]

    return {
        "id": first_profile_id,
        "name": profile.get("name", ""),
        "url": profile.get("url", ""),
        "thumbSrc": profile.get("thumbSrc", ""),
        "gender": profile.get("gender", "")
    }


def cmt_gr_pst(cookie,
               grid,
               postIDD,
               ctn,
               user_id,
               fb_dtsg,
               rev,
               req,
               a,
               jazoest,
               uidtag=None,
               nametag=None):
    try:
        if not all([user_id, fb_dtsg, jazoest]):
            print("Thiếu user_id, fb_dtsg hoặc jazoest")
            return False

        pstid_enc = base64.b64encode(f"feedback:{postIDD}".encode()).decode()

        client_mutation_id = str(round(random.random() * 19))
        session_id = get_guid()
        crt_time = int(time.time() * 1000)

        variables = {
            "feedLocation": "DEDICATED_COMMENTING_SURFACE",
            "feedbackSource": 110,
            "groupID": grid,
            "input": {
                "client_mutation_id": client_mutation_id,
                "actor_id": user_id,
                "attachments": None,
                "feedback_id": pstid_enc,
                "formatting_style": None,
                "message": {
                    "ranges": [],
                    "text": ctn
                },
                "attribution_id_v2":
                f"SearchCometGlobalSearchDefaultTabRoot.react,comet.search_results.default_tab,tap_search_bar,{crt_time},775647,391724414624676,,",
                "vod_video_timestamp": None,
                "is_tracking_encrypted": True,
                "tracking": [],
                "feedback_source": "DEDICATED_COMMENTING_SURFACE",
                "session_id": session_id
            },
            "inviteShortLinkKey": None,
            "renderLocation": None,
            "scale": 3,
            "useDefaultActor": False,
            "focusCommentID": None,
            "__relay_internal__pv__IsWorkUserrelayprovider": False
        }

        if uidtag and nametag:
            name_position = ctn.find(nametag)
            if name_position != -1:
                variables["input"]["message"]["ranges"] = [{
                    "entity": {
                        "id": uidtag
                    },
                    "length":
                    len(nametag),
                    "offset":
                    name_position
                }]

        payload = {
            'av': user_id,
            '__crn': 'comet.fbweb.CometGroupDiscussionRoute',
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'useCometUFICreateCommentMutation',
            'variables': json.dumps(variables),
            'server_timestamps': 'true',
            'doc_id': '24323081780615819'
        }

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Origin': 'https://www.facebook.com',
            'Referer': f'https://www.facebook.com/groups/{grid}',
            'User-Agent': 'python-http/0.27.0'
        }

        response = requests.post('https://www.facebook.com/api/graphql',
                                 data=payload,
                                 headers=headers)
        print(f"Mã trạng thái cho bài {postIDD}: {response.status_code}")

        if response.status_code == 200:
            try:
                json_response = response.json()
                if 'errors' in json_response:
                    print(f"Lỗi GraphQL: {json_response['errors']}")
                    return False
                if 'data' in json_response and 'comment_create' in json_response[
                        'data']:
                    print("Bình luận đã được đăng")
                    return True
                print("Không tìm thấy comment_create trong phản hồi")
                return False
            except ValueError:
                print("Phản hồi JSON không hợp lệ")
                return False
        else:
            return False
    except Exception as e:
        print(f"Lỗi khi gửi bình luận: {e}")
        return False


def extract_post_group_id(post_link):
    post_match = re.search(r'facebook\.com/.+/permalink/(\d+)', post_link)
    group_match = re.search(r'facebook\.com/groups/(\d+)', post_link)
    if not post_match or not group_match:
        return None, None
    return post_match.group(1), group_match.group(1)


# ========== BUTTON VIEWS ==========


class MenuView(View):

    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="📋 Hướng Dẫn",
                       style=ButtonStyle.primary,
                       emoji="📋")
    async def hdan_button(self, interaction: discord.Interaction,
                          button: Button):
        await interaction.response.defer()
        embed = discord.Embed(title="『 **Hướng Dẫn Dùng Lệnh**』",
                              description=f"""  
**`Hướng Dẫn`**

**`!treo <idbox> <cookie> <file.txt> <delay>`**
**`!nhay <idbox> <cookie> <delay>`**
**`!nhayicon <idbox> <cookie> <icon> <delay`**
**`!nhaytag <idbox> <cookie> <id> <delay>`**
**`!nhay2c <idbox> <cookie> <delay>`**
**`!treoso <idbox> <cookie> <delay>`**
**`!ideamess <idbox> <cookie> <delay>`**
**`!codelag <idbox> <cookie> <delay>`**
**`!nhaytop <cookie> <delay>`**
**`!treotop <cookie> <delay> <file.txt>`**
**`!nhaynamebox <idbox> <cookie> <delay>`**

**`!listbox <cookie>`**
""",
                              color=0xB8F0FF)
        await interaction.followup.send(embed=embed, ephemeral=True)


# ========== ADMIN COMMANDS ==========


@bot.command()
async def add(ctx, member: str):
    if ctx.author.id != IDADMIN_GOC:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(1)

        try:
            if member.startswith('<@') and member.endswith('>'):
                member_id = int(member[2:-1].replace('!', ''))
            else:
                member_id = int(member)

            try:
                target_member = await bot.fetch_user(member_id)
            except discord.NotFound:
                return await ctx.send("Không tìm thấy người dùng với ID này.")

            if target_member.id in admins:
                return await ctx.send("Người này đã là Owner rồi.")

            admins.append(target_member.id)
            await ctx.send(
                f"Đã thêm `{target_member.name}` (ID: {target_member.id}) vào danh sách Owner."
            )

        except ValueError:
            await ctx.send(
                "Vui lòng nhập ID hợp lệ hoặc đề cập (@tag) người dùng.")


@bot.command()
async def xoa(ctx, member: str):
    if ctx.author.id != IDADMIN_GOC:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(1)

        try:
            if member.startswith('<@') and member.endswith('>'):
                member_id = int(member[2:-1].replace('!', ''))
            else:
                member_id = int(member)

            if member_id == IDADMIN_GOC:
                return await ctx.send("Không thể xóa admin gốc.")

            if member_id in admins:
                try:
                    target_member = await bot.fetch_user(member_id)
                    name = target_member.name
                except:
                    name = str(member_id)

                admins.remove(member_id)
                await ctx.send(
                    f"Đã xoá `{name}` (ID: {member_id}) khỏi danh sách Owner.")
            else:
                await ctx.send("Người này không có trong danh sách Owner.")

        except ValueError:
            await ctx.send(
                "Vui lòng nhập ID hợp lệ hoặc đề cập (@tag) người dùng.")


@bot.command()
async def list(ctx):
    async with ctx.typing():
        await asyncio.sleep(1)

        msg = "**Danh sách Owner hiện tại:**\n"
        for admin_id in admins:
            try:
                user = await bot.fetch_user(admin_id)
                if admin_id == IDADMIN_GOC:
                    msg += f"- <@{IDADMIN_GOC}> **(Admin Gốc)**\n"
                else:
                    msg += f"- **{user.name} - {admin_id} (Owner)**\n"
            except Exception as e:
                msg += f"- **{admin_id} (Không tìm được tên) (Owner)**\n"
        await ctx.send(msg)


@bot.command()
async def setfile(ctx):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền.")

    async with ctx.typing():
        await asyncio.sleep(1)

        if not ctx.message.attachments:
            return await ctx.send("Vui lòng đính kèm file.")
        admin_id = str(ctx.author.id)
        file = ctx.message.attachments[0]
        filename = file.filename
        os.makedirs(f"data/{admin_id}", exist_ok=True)
        path = f"data/{admin_id}/{filename}"
        await file.save(path)
        await ctx.send(f"Đã lưu file `{filename}` vào thư mục của bạn.")


@bot.command()
async def xemfileset(ctx):
    async with ctx.typing():
        await asyncio.sleep(1)

        admin_id = str(ctx.author.id)
        folder = f"data/{admin_id}"
        if not os.path.exists(folder):
            return await ctx.send("Bạn chưa lưu file nào.")
        files = os.listdir(folder)
        if not files:
            return await ctx.send("Bạn chưa lưu file nào.")
        msg = f"**Danh sách file của `{ctx.author.name}`:**\n"
        for fname in files:
            path = os.path.join(folder, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    preview = f.read(100).replace('\n', ' ')
                    msg += f"`{fname}`: {preview}...\n"
            except:
                msg += f"`{fname}`: (Không đọc được nội dung)\n"
        await ctx.send(msg)


# ========== FACEBOOK COMMANDS ==========


@bot.command()
async def treo(ctx, id_box: str, cookie: str, filename: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        admin_id = str(ctx.author.id)
        file_path = f"data/{admin_id}/{filename}"

        if not os.path.exists(file_path):
            return await ctx.send(
                f"File `{filename}` không tồn tại trong thư mục của bạn.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        with open(file_path, 'r', encoding='utf-8') as f:
            message_body = f.read().strip()

        print(
            f"[+] Đã bắt đầu spam box {id_box} với file {filename} (delay: {speed}s)"
        )

        task_id = f"ngonmess_{id_box}_{time.time()}"

        async def spam_loop_task():
            while True:
                success = send_message(id_box, fb_dtsg, jazoest, cookie,
                                       message_body)
                if success:
                    print(f"[+] Đã gửi 1 tin nhắn vào box {id_box}")
                else:
                    print(f"[!] Gửi thất bại vào box {id_box}")
                await asyncio.sleep(speed)

        task = asyncio.create_task(spam_loop_task())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time()
        }
        await ctx.send(
            f"✅ **Đã tạo task treo thành công!**\n📦 Box: `{id_box}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def nhay(ctx, id_box: str, cookie: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "nhay.txt"
        if not os.path.exists(path):
            return await ctx.send(
                "Không tìm thấy file `nhay.txt` trong thư mục data.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        task_id = f"nhay_{id_box}_{time.time()}"

        async def loop_nhay():
            index = 0
            while True:
                send_message(id_box, fb_dtsg, jazoest, cookie, lines[index])
                index = (index + 1) % len(lines)
                await asyncio.sleep(speed)

        task = asyncio.create_task(loop_nhay())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time()
        }
        await ctx.send(
            f"✅ **Đã tạo task nhay thành công!**\n📦 Box: `{id_box}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def codelag(ctx, id_box: str, cookie: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "nhay.txt"
        if not os.path.exists(path):
            return await ctx.send("Không tìm thấy file `nhay.txt`.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        icon = "💀"  # Biểu tượng cố định
        task_id = f"codelag_{id_box}_{time.time()}"

        async def loop_codelag():
            index = 0
            while True:
                message = f"{lines[index]} {icon}"
                send_message(id_box, fb_dtsg, jazoest, cookie, message)
                index = (index + 1) % len(lines)
                await asyncio.sleep(speed)

        task = asyncio.create_task(loop_codelag())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time()
        }
        await ctx.send(
            f"✅ **Đã tạo task codelag thành công!**\n📦 Box: `{id_box}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def nhaytop(ctx, cookie: str, delay: float):
    if ctx.author.id not in admins:
        await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        return

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "chui.txt"
        if not os.path.exists(path):
            await ctx.send("Không tìm thấy file `nhay.txt`.")
            return

        await ctx.send(
            "Vui lòng nhập link bài viết (ví dụ: https://facebook.com/groups/123/permalink/456):"
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            post_link = msg.content.strip()
        except asyncio.TimeoutError:
            await ctx.send("Hết thời gian chờ nhập link bài viết.")
            return

        post_id, group_id = extract_post_group_id(post_link)
        if not post_id or not group_id:
            await ctx.send(
                "Link bài viết không hợp lệ hoặc không tìm được group_id.")
            return

        cookie = normalize_cookie(cookie)

        user_id, fb_dtsg, rev, req, a, jazoest = get_uid_fbdtsg(cookie)
        if not user_id or not fb_dtsg or not jazoest:
            await ctx.send("Cookie không hợp lệ hoặc không lấy được thông tin."
                           )
            return

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            await ctx.send("File `nhay.txt` rỗng.")
            return

        task_id = f"nhaytop_{post_id}_{time.time()}"

        async def loop_nhaytop():
            index = 0
            while True:
                message = lines[index]
                success = cmt_gr_pst(cookie, group_id, post_id, message,
                                     user_id, fb_dtsg, rev, req, a, jazoest)
                if success:
                    print(f"[+] Đã gửi bình luận vào bài {post_id}: {message}")
                else:
                    print(f"[!] Gửi bình luận thất bại vào bài {post_id}")
                index = (index + 1) % len(lines)
                await asyncio.sleep(delay)

        task = asyncio.create_task(loop_nhaytop())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time(),
            'post_id': post_id,
            'group_id': group_id
        }
        await ctx.send(
            f"✅ **Đã tạo task nhaytop thành công!**\n📝 Post: `{post_id}`\n⏱️ Delay: `{delay}s`"
        )


@bot.command()
async def treoso(ctx, id_box: str, cookie: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "so.txt"
        if not os.path.exists(path):
            return await ctx.send(
                "Không tìm thấy file `nhay.txt` trong thư mục data.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        task_id = f"so_{id_box}_{time.time()}"

        async def loop_nhay():
            index = 0
            while True:
                send_message(id_box, fb_dtsg, jazoest, cookie, lines[index])
                index = (index + 1) % len(lines)
                await asyncio.sleep(speed)

        task = asyncio.create_task(loop_nhay())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time()
        }
        await ctx.send(
            f"✅ **Đã tạo task treoso thành công!**\n📦 Box: `{id_box}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def ideamess(ctx, id_box: str, cookie: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "chui.txt"
        if not os.path.exists(path):
            return await ctx.send(
                "Không tìm thấy file `nhay.txt` trong thư mục data.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        task_id = f"cay_{id_box}_{time.time()}"

        async def loop_nhay():
            index = 0
            while True:
                send_message(id_box, fb_dtsg, jazoest, cookie, lines[index])
                index = (index + 1) % len(lines)
                await asyncio.sleep(speed)

        task = asyncio.create_task(loop_nhay())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time()
        }
        await ctx.send(
            f"✅ **Đã tạo task ideamess thành công!**\n📦 Box: `{id_box}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def nhay2c(ctx, id_box: str, cookie: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "2c.txt"
        if not os.path.exists(path):
            return await ctx.send(
                "Không tìm thấy file `nhay.txt` trong thư mục data.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        task_id = f"2c_{id_box}_{time.time()}"

        async def loop_nhay():
            index = 0
            while True:
                send_message(id_box, fb_dtsg, jazoest, cookie, lines[index])
                index = (index + 1) % len(lines)
                await asyncio.sleep(speed)

        task = asyncio.create_task(loop_nhay())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time()
        }
        await ctx.send(
            f"✅ **Đã tạo task nhay2c thành công!**\n📦 Box: `{id_box}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def nhaytag(ctx, id_box: str, cookie: str, tag_uid: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "nhay.txt"
        if not os.path.exists(path):
            return await ctx.send(
                "Không tìm thấy file `nhay.txt` trong thư mục data.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        tag_name = None
        try:
            user_id, fb_dtsg, rev, req, a, jazoest = get_uid_fbdtsg(cookie)
            if user_id and fb_dtsg:
                info = get_info(tag_uid, cookie, fb_dtsg, a, req, rev)
                if "error" not in info:
                    tag_name = info.get("name")
        except:
            pass

        if not tag_name:
            await ctx.send(
                "Không thể lấy tên từ ID, vui lòng nhập tên thủ công (ví dụ: Nguyen Van A):"
            )

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await bot.wait_for('message', timeout=30.0, check=check)
                tag_name = msg.content.strip()
                if not tag_name:
                    return await ctx.send("Tên không được để trống!")
            except asyncio.TimeoutError:
                return await ctx.send("Hết thời gian chờ nhập tên.")

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        task_id = f"nhaytag_{id_box}_{time.time()}"

        async def loop_nhaytag():
            index = 0
            while True:
                message = f"{lines[index]} @{tag_name}"
                success = send_message(id_box, fb_dtsg, jazoest, cookie,
                                       message, tag_uid, tag_name)
                index = (index + 1) % len(lines)
                await asyncio.sleep(speed)

        task = asyncio.create_task(loop_nhaytag())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time(),
            'tag_uid': tag_uid,
            'tag_name': tag_name
        }
        await ctx.send(
            f"✅ **Đã tạo task nhaytag thành công!**\n📦 Box: `{id_box}`\n🏷️ Tag: `{tag_name}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def nhayicon(ctx, id_box: str, cookie: str, icon: str, speed: float):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(2)

        path = "nhayicon.txt"
        if not os.path.exists(path):
            return await ctx.send(
                "Không tìm thấy file `nhay.txt` trong thư mục data.")

        fb_dtsg, jazoest = get_fb_dtsg_jazoest(cookie, id_box)
        if not fb_dtsg:
            return await ctx.send(
                "Cookie không hợp lệ hoặc không lấy được thông tin.")

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        task_id = f"nhayicon_{id_box}_{time.time()}"

        async def loop_nhayicon():
            index = 0
            while True:
                message = f"{lines[index]}{icon}"
                success = send_message(id_box, fb_dtsg, jazoest, cookie,
                                       message)
                index = (index + 1) % len(lines)
                await asyncio.sleep(speed)

        task = asyncio.create_task(loop_nhayicon())
        running_tasks[task_id] = task
        task_info[task_id] = {
            'admin_id': ctx.author.id,
            'start_time': time.time()
        }
        await ctx.send(
            f"✅ **Đã tạo task nhayicon thành công!**\n📦 Box: `{id_box}`\n🎨 Icon: `{icon}`\n⏱️ Delay: `{speed}s`"
        )


@bot.command()
async def treotop(ctx, cookie: str, delay: float, filename: str):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này")

    async with ctx.typing():
        await asyncio.sleep(2)

        file_path = f"data/{ctx.author.id}/{filename}"
        if not os.path.exists(file_path):
            return await ctx.send(
                f"Không tìm thấy file `{filename}` trong thư mục của bạn")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_content = f.read().strip()

            if len(full_content) > 8000:
                return await ctx.send("Nội dung quá dài (tối đa 8000 ký tự)")
            if not full_content:
                return await ctx.send("File không có nội dung")
        except UnicodeDecodeError:
            return await ctx.send("Lỗi định dạng file (dùng UTF-8)")
        except Exception as e:
            return await ctx.send(f"Lỗi đọc file: {str(e)}")

        await ctx.send(
            "🔗 Nhập link bài viết Facebook (VD: https://facebook.com/groups/123/permalink/456):"
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            post_link = msg.content.strip()
        except asyncio.TimeoutError:
            return await ctx.send("Hết thời gian chờ nhập link")

        post_id, group_id = extract_post_group_id(post_link)
        if not post_id or not group_id:
            return await ctx.send("Link bài viết không hợp lệ")

        cookie = normalize_cookie(cookie)
        user_id, fb_dtsg, rev, req, a, jazoest = get_uid_fbdtsg(cookie)
        if not user_id or not fb_dtsg:
            return await ctx.send("Cookie không hợp lệ")

        task_id = f"treotop_full_{post_id}_{int(time.time())}"

        async def spam_task():
            while task_id in running_tasks:
                try:
                    success = cmt_gr_pst(cookie=cookie,
                                         grid=group_id,
                                         postIDD=post_id,
                                         ctn=full_content,
                                         user_id=user_id,
                                         fb_dtsg=fb_dtsg,
                                         rev=rev,
                                         req=req,
                                         a=a,
                                         jazoest=jazoest)

                    if success:
                        print(f"[✅] Đã Treo Thành Công Vào Post {post_id}")
                    else:
                        print(f"[❌] Gửi thất bại post {post_id}")

                    await asyncio.sleep(delay)
                except Exception as e:
                    print(f"[🔥] Lỗi: {str(e)}")
                    await asyncio.sleep(10)

        running_tasks[task_id] = asyncio.create_task(spam_task())
        task_info[task_id] = {
            'admin_id':
            ctx.author.id,
            'start_time':
            time.time(),
            'post_id':
            post_id,
            'group_id':
            group_id,
            'file_path':
            file_path,
            'content_preview':
            full_content[:100] +
            '...' if len(full_content) > 100 else full_content,
            'type':
            'treotop_full'
        }

        await ctx.send(f"✅ **Đã Bắt Đầu Treo Top!**\n"
                       f"📁 File: `{filename}`\n"
                       f"📝 Post: `{post_id}`\n"
                       f"⏱️ Delay: `{delay}s`\n"
                       f"🛑 Dừng: **`.stoptask {len(running_tasks)}`**")


# ========== TASK MANAGEMENT COMMANDS ==========


@bot.command()
async def stoptask(ctx, task_number: str = None):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    is_root_admin = (ctx.author.id == IDADMIN_GOC)
    user_tasks = []

    for task_id, info in task_info.items():
        if is_root_admin or info['admin_id'] == ctx.author.id:
            task_type = task_id.split('_')[0]
            box_id = task_id.split('_')[1]
            duration = str(datetime.now() -
                           datetime.fromtimestamp(info['start_time'])).split(
                               '.')[0]

            try:
                admin = await bot.fetch_user(info['admin_id'])
                admin_name = admin.name
            except:
                admin_name = f"ID {info['admin_id']}"

            user_tasks.append({
                'id': task_id,
                'type': task_type,
                'box_id': box_id,
                'duration': duration,
                'admin': admin_name,
                'admin_id': info['admin_id']
            })

    if not user_tasks:
        return await ctx.send("Không có task nào đang chạy.")

    if task_number is not None:
        if task_number.lower() == 'all':
            stopped_count = 0
            for task in user_tasks:
                if is_root_admin or task['admin_id'] == ctx.author.id:
                    if task['id'] in running_tasks:
                        running_tasks[task['id']].cancel()
                        del running_tasks[task['id']]
                        del task_info[task['id']]
                        stopped_count += 1
            return await ctx.send(f"Đã dừng {stopped_count} task.")

        try:
            task_index = int(task_number) - 1
            if 0 <= task_index < len(user_tasks):
                task = user_tasks[task_index]
                if not is_root_admin and task['admin_id'] != ctx.author.id:
                    return await ctx.send("Bạn không có quyền dừng task này!")

                if task['id'] in running_tasks:
                    running_tasks[task['id']].cancel()
                    del running_tasks[task['id']]
                    del task_info[task['id']]
                    return await ctx.send(f"Đã dừng task số {task_number}.")
            return await ctx.send("Số task không hợp lệ.")
        except ValueError:
            return await ctx.send("Vui lòng nhập số task hoặc 'all'.")

    msg = "**Danh sách task đang chạy:**\n"
    msg += "(Bạn là admin gốc, có thể dừng mọi task)\n" if is_root_admin else ""

    for i, task in enumerate(user_tasks, 1):
        msg += f"{i}. {task['type']} - Box: {task['box_id']} - Owner: {task['admin']} (Đã chạy: {task['duration']})\n"

    msg += "\nNhập `!stoptask [số]` để dừng task hoặc `!stoptask all` để dừng tất cả"
    await ctx.send(msg)


@bot.command()
async def danhsachtask(ctx):
    if ctx.author.id not in admins:
        return await ctx.send("Bạn không có quyền sử dụng lệnh này.")

    async with ctx.typing():
        await asyncio.sleep(1)

        is_root_admin = (ctx.author.id == IDADMIN_GOC)
        user_tasks = []

        for task_id, info in task_info.items():
            if is_root_admin or info['admin_id'] == ctx.author.id:
                task_type = task_id.split('_')[0]
                box_id = task_id.split('_')[1]
                duration = str(
                    datetime.now() -
                    datetime.fromtimestamp(info['start_time'])).split('.')[0]

                try:
                    admin = await bot.fetch_user(info['admin_id'])
                    admin_name = admin.name
                except:
                    admin_name = f"ID {info['admin_id']}"

                user_tasks.append({
                    'id': task_id,
                    'type': task_type,
                    'box_id': box_id,
                    'duration': duration,
                    'admin': admin_name,
                    'admin_id': info['admin_id']
                })

        if not user_tasks:
            return await ctx.send("Không có task nào đang chạy.")

        msg = "**Danh sách task đang chạy:**\n"
        msg += "(Bạn là admin gốc, có thể dừng mọi task)\n" if is_root_admin else ""

        for i, task in enumerate(user_tasks, 1):
            msg += f"{i}. {task['type']} - Box: {task['box_id']} - Owner: {task['admin']} (Đã chạy: {task['duration']})\n"

        msg += "\nNhập `!stoptask [số]` để dừng task hoặc `!stoptask all` để dừng tất cả"
        await ctx.send(msg)


# ========== MENU COMMANDS ==========

@bot.command()
async def menu(ctx):
    # Tạo embed với font chữ đậm và rõ ràng hơn
    embed = discord.Embed(
        title="🎯 **BOT XUANTHANG MENU** 🎯",
        description="**Developer: XUAN THANG**\n────────────────────",
        color=0x00FF00  # Màu xanh lá nổi bật
    )

    # Ảnh lớn làm banne
    embed.set_image(url="https://c.tenor.com/32qrBWDoLiAAAAAd/anime.gif")

    # Phần lệnh Owner - font chữ được làm nổi bật
    embed.add_field(
        name="**👑 QUẢN LÝ OWNER**",
        value=(
            "```diff\n"
            "+ !add    - Thêm Owner mới\n"
            "+ !xoa    - Xóa Owner\n" 
            "+ !list   - Danh sách Owner\n"
            "```"
        ),
        inline=False
    )

    # Phần lệnh Bot - font chữ được làm nổi bật
    embed.add_field(
        name="**🤖 LỆNH BOT**",
        value=(
            "```css\n"
            "[!treo]      - Treo mess bất tử\n"
            "[!nhay]      - Nhây mess liên tục\n"
            "[!nhayicon]  - Nhây icon mess\n"
            "[!nhaytag]   - Nhây tag mess\n"
            "[!nhay2c]    - Nhây 2 chữ\n"
            "[!treoso]    - Treo sớ super\n"
            "[!ideamess]  - Nhây cay mess\n"
            "[!codelag]   - Code lag mess\n"
            "[!nhaytop]   - Nhây top vip\n"
            "[!treotop]   - Treo top vip\n"
            "[!listbox]   - Show box cookie\n"
            "[!setfile]   - Gửi kèm file\n"
            "[!xemfileset]- Xem file đã lưu\n"
            "[!danhsachtask] - Danh sách task\n"
            "[!stoptask]  - Dừng task\n"
            "```"
        ),
        inline=False
    )

    # Footer với thông tin bổ sung
    embed.set_footer(text="📌 Sử dụng !help <lệnh> để biết thêm chi tiết")

    view = MenuView()
    await ctx.send(embed=embed, view=view)

@bot.command()
async def hdan(ctx):
    embed = discord.Embed(title="『 **Hướng Dẫn Dùng Lệnh**』",
                          description=f"""  
**`Hướng Dẫn`**

**`!treo <idbox> <cookie> <file.txt> <delay>`**
**`!nhay <idbox> <cookie> <delay>`**
**`!nhayicon <idbox> <cookie> <icon> <delay`**
**`!nhaytag <idbox> <cookie> <id> <delay>`**
**`!nhay2c <idbox> <cookie> <delay>`**
**`!treoso <idbox> <cookie> <delay>`**
**`!ideamess <idbox> <cookie> <delay>`**
**`!codelag <idbox> <cookie> <delay>`**
**`!nhaytop <cookie> <delay>`**
**`!treotop <cookie> <delay> <file.txt>`**

**`!listbox <cookie>`**
""",
                          color=0xB8F0FF)

    await ctx.send(embed=embed)


bot.run(TOKEN)
