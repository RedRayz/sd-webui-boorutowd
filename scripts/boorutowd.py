import modules.scripts as scripts
import gradio as gr
import os
import requests

from modules import script_callbacks

def convert_to_wd(
        booru_tags: str, 
        booru_url: str,
        remove_meta_artist: bool
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
                source = raw_json["tag_string"]
        except:
            print("Failed to fetch danbooru tags.")
            return "URLからdanbooruタグを取得できません。"
    else:
        source = booru_tags

    if not source:
        return "入力が空です。"

    if os.path.exists("removal-list.txt") and remove_meta_artist:
        f = open('removal-list.txt', 'r', encoding='UTF-8') 
        removal = f.read()
        f.close()
        removal = removal.replace("\r\n", "\n")
        tags = removal.split("\n")
        sourceTags = source.split(" ")
        for i, tag in enumerate(tags):
            for j, src in enumerate(sourceTags):
                if(tag == src and tag):
                    # print(f"Found removal tag: {src}")
                    sourceTags[j] = ''

        for i, tag in enumerate(sourceTags):
            if i < (len(sourceTags) - 1) and tag:
                sourceTags[i] += ", "

        dest = ''.join(sourceTags)
    else:
        dest = source.replace(" ", ", ")

    
    dest = dest.replace("_", " ")
    # 制御文字のエスケープ
    dest = dest.replace("\\", "\\\\")
    dest = dest.replace("(", "\(")
    dest = dest.replace(")", "\)")

    dest = dest.replace("<", "\<")
    dest = dest.replace(">", "\>")

    dest = dest.replace("|", "\|")

    dest = dest.replace("[", "\[")
    dest = dest.replace("]", "\]")
    

    return dest


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as ui_component:
        with gr.Row():
            danbooru_url = gr.Textbox(label="Danbooru URL", lines=1)
            booru_tags_input = gr.Textbox(label="Booru tags(Danbooru URLが優先されます)", lines=8)
            remove_meta_and_artist = gr.Checkbox(label="MetaとArtist(一部のみ)を削除")
            convert_button = gr.Button("変換", variant='primary')
            output = gr.Textbox(label="結果(テキストボックス右上の四角いアイコンのボタンを押してコピー)", lines=8, show_copy_button=True)
            convert_button.click(fn=convert_to_wd, inputs=[booru_tags_input, danbooru_url, remove_meta_and_artist], outputs=output)
        return [(ui_component, "Booru WD", "extension_boorutowd_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
