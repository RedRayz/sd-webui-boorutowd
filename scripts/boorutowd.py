from modules.paths import extensions_dir
import gradio as gr
import os
import requests
import re
import contextlib

from modules import script_callbacks
from modules import scripts

MYEXTENSION_DIR = f"{extensions_dir}/sd-webui-boorutowd"

def convert_to_wd(
        booru_tags: str, 
        booru_url: str,
        remove_meta_artist: bool,
        to_animagine_style: bool,
        ):
    source = ""
    dest = ""
    if booru_url:
        try:
            burl = booru_url + ".json"
            with requests.get(
                url=burl,
                headers={'user-agent': 'my-app/1.0.0'}
            ) as r:
                raw_json = r.json()
                if not to_animagine_style:
                    if remove_meta_artist:
                        txt = raw_json["tag_string_character"]
                        if txt:
                            source += f"{txt} "
                        txt = raw_json["tag_string_copyright"]
                        if txt:
                            source += f"{txt} "
                        txt = raw_json["tag_string_general"]
                        if txt:
                            source += f"{txt} "
                    else:
                        source = raw_json["tag_string"]
                else:
                    pattern = "[1-6]\\+?(girl|boy)s?"
                    repatter = re.compile(pattern)
                    rawtag_general = raw_json["tag_string_general"]
                    general_tags_list = rawtag_general.split(' ')
                    # girl/boyを先に追加
                    for i, tag in enumerate(general_tags_list):
                        is_match = repatter.match(tag)
                        if is_match:
                            source += f"{tag} "
                    # character
                    rawtag_character = raw_json["tag_string_character"]
                    if rawtag_character:
                        source += f"{rawtag_character} "
                    # copyright
                    rawtag_copyright = raw_json["tag_string_copyright"]
                    if rawtag_copyright:
                        source += f"{rawtag_copyright} "
                    # girl/boy以外のgeneralタグ
                    for i, tag in enumerate(general_tags_list):
                        is_match = repatter.match(tag)
                        if not is_match:
                            source += f"{tag} "
                    if not remove_meta_artist:
                        txt = raw_json["tag_string_artist"]
                        if txt:
                            source += f"{txt} "
                        txt = raw_json["tag_string_meta"]
                        if txt:
                            source += f"{txt} "
        except:
            print("Failed to fetch danbooru tags.")
            return "Could not load danbooru tags from the URL / URLからdanbooruタグを取得できませんでした。"
    else:
        source = booru_tags

    if not source:
        return "Input is empty. / 入力が空です。"

    source = source.strip()


    if os.path.exists(f"{MYEXTENSION_DIR}/removal-list.txt") and remove_meta_artist and not booru_url:
        f = open(f"{MYEXTENSION_DIR}/removal-list.txt", 'r', encoding='UTF-8') 
        removal = f.read()
        f.close()
        removal = removal.replace('\r\n', '\n')
        tags = removal.split('\n')
        sourceTags = source.split(' ')
        for i, tag in enumerate(tags):
            for j, src in enumerate(sourceTags):
                if(tag == src and tag) or ("user_" in src):
                    # print(f"Found removal tag: {src}")
                    sourceTags[j] = ''

        for i, tag in enumerate(sourceTags):
            if i < (len(sourceTags) - 1) and tag:
                sourceTags[i] += ", "

        dest = ''.join(sourceTags)
    else:
        dest = source.replace(' ', ", ")

    
    dest = dest.replace('_', ' ')
    # 制御文字のエスケープ
    dest = dest.replace('\\', "\\\\")
    dest = dest.replace('(', "\(")
    dest = dest.replace(')', "\)")

    dest = dest.replace('<', "\<")
    dest = dest.replace('>', "\>")

    dest = dest.replace('|', "\|")

    dest = dest.replace('[', "\[")
    dest = dest.replace(']', "\]")
    

    return dest

def send_text(old_text, new_text):
    if not old_text:
        return new_text
    return old_text + " " + new_text

class BooruToWd(scripts.Script):
    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return "Booru to WD"

    def show(self, is_img2img):
        return scripts.AlwaysVisible
    
    def ui(self, is_img2img):
        with gr.Accordion(label="Booru to WD", open=False, elem_id="boorutowd_ui"):
            with gr.Column():
                danbooru_url = gr.Textbox(label="Danbooru URL", lines=1)
                convert_to_animagine_style = gr.Checkbox(label="Animagineスタイルにする(URLからのみ機能)/Animagine style(only works for the URL)")
                booru_tags_input = gr.Textbox(label="Booru tags(URLが優先されます/URL takes precedence)", lines=8)
                remove_meta_and_artist = gr.Checkbox(label="Meta、Artistとuser_xxxを削除/Remove meta, artist, and user_xxx")
                convert_button = gr.Button("変換/Convert", variant='primary')
                output = gr.Textbox(label="結果/Result", lines=8, show_copy_button=True)
                convert_button.click(fn=convert_to_wd, inputs=[booru_tags_input, danbooru_url, remove_meta_and_artist, convert_to_animagine_style], outputs=output)
                send_to_prompt = gr.Button("結果をプロンプトに送信/Send to prompt", variant='secondary')
                with contextlib.suppress(AttributeError):
                    if is_img2img:
                        send_to_prompt.click(fn=send_text, inputs=[self.boxxIMG, output], outputs=self.boxxIMG)
                    else:
                        send_to_prompt.click(fn=send_text, inputs=[self.boxx, output], outputs=self.boxx)
            return [danbooru_url, convert_to_animagine_style, booru_tags_input, remove_meta_and_artist, convert_button, output, send_to_prompt]

    def after_component(self, component, **kwargs):
        if kwargs.get("elem_id") == "txt2img_prompt":
            self.boxx = component
        if kwargs.get("elem_id") == "img2img_prompt":
            self.boxxIMG = component