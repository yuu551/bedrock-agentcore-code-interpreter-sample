import json
import boto3
import base64
import uuid
import os
from datetime import datetime
from typing import Dict, Any
from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.tools.code_interpreter_client import code_session

app = BedrockAgentCoreApp()

# S3設定
S3_BUCKET = os.environ.get('S3_BUCKET', 'your-s3-bucket-name')
S3_REGION = os.environ.get('AWS_REGION', 'us-west-2')

# S3クライアントを初期化（エラーハンドリング付き）
try:
    s3_client = boto3.client('s3', region_name=S3_REGION)
    S3_AVAILABLE = True
except Exception as e:
    print(f"S3 client initialization failed: {e}")
    S3_AVAILABLE = False

# システムプロンプトを短縮
SYSTEM_PROMPT = """You are a data analysis expert AI assistant.

Key principles:
1. Verify all claims with code
2. Use execute_python tool for calculations
3. Show your work through code execution
4. ALWAYS provide S3 URLs when graphs are generated

When you create visualizations:
- Graphs are automatically uploaded to S3
- Share the S3 URLs with users (valid for 1 hour)
- Clearly indicate which figure each URL represents
- IMPORTANT: Only use matplotlib for plotting. DO NOT use seaborn or other plotting libraries
- Use matplotlib's built-in styles instead of seaborn themes

Available libraries:
- pandas, numpy for data manipulation
- matplotlib.pyplot for visualization (use ONLY this for plotting)
- Basic Python libraries (json, datetime, etc.)

The execute_python tool returns JSON with:
- isError: boolean indicating if error occurred
- structuredContent: includes image_urls (S3 links) or images (base64 fallback)
- debug_info: debugging information about code execution

Always mention generated graph URLs in your response."""

@tool
def execute_python(code: str, description: str = "") -> str:
    """Execute Python code and capture any generated graphs"""
    
    if description:
        code = f"# {description}\n{code}"
    
    # Minimal image capture code
    img_code = f"""
import matplotlib
matplotlib.use('Agg')
{code}
import matplotlib.pyplot as plt,base64,io,json
imgs=[]
for i in plt.get_fignums():
 b=io.BytesIO()
 plt.figure(i).savefig(b,format='png')
 b.seek(0)
 imgs.append({{'i':i,'d':base64.b64encode(b.read()).decode()}})
if imgs:print('_IMG_'+json.dumps(imgs)+'_END_')
"""
    
    try:
        # Code Interpreterセッションを開始
        with code_session("us-west-2") as code_client:
            response = code_client.invoke("executeCode", {
                "code": img_code,
                "language": "python",
                "clearContext": False
            })
            result = None
            for event in response["stream"]:
                result = event["result"]
            if result is None:
                result = {
                    "isError": True,
                    "structuredContent": {
                        "stdout": "",
                        "stderr": "No result events from Code Interpreter",
                        "exitCode": 1
                    }
                }
        
        # デバッグ情報を追加
        result["debug_info"] = {
            "code_size": len(img_code),
            "original_code_size": len(code),
            "img_code_preview": img_code[-200:],
        }
        
        # 標準出力を取得
        stdout = result.get("structuredContent", {}).get("stdout", "")
        
        # デバッグ情報を拡張
        result["debug_info"]["stdout_length"] = len(stdout)
        result["debug_info"]["img_marker_found"] = "_IMG_" in stdout
        result["debug_info"]["stdout_tail"] = stdout[-300:] if len(stdout) > 300 else stdout
        
        if "_IMG_" in stdout and "_END_" in stdout:
            try:
                start = stdout.find("_IMG_") + 5
                end = stdout.find("_END_")
                img_json = stdout[start:end]
                imgs = json.loads(img_json)
                
                # デバッグ情報にイメージ数を追加
                result["debug_info"]["images_found"] = len(imgs)
                
                # 標準出力をクリーンアップ
                clean_out = stdout[:stdout.find("_IMG_")].strip()
                
                # S3へのアップロードを試行
                image_urls = []
                if S3_AVAILABLE and imgs:
                    for img_data in imgs:
                        try:
                            # 画像データをデコード
                            img_bytes = base64.b64decode(img_data['d'])
                            
                            # ユニークなファイル名を生成
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            file_key = f"agent-outputs/{timestamp}_fig{img_data['i']}.png"
                            
                            # S3にアップロード
                            s3_client.put_object(
                                Bucket=S3_BUCKET,
                                Key=file_key,
                                Body=img_bytes,
                                ContentType='image/png'
                            )
                            
                            # 署名付きURLを生成（1時間有効）
                            url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': S3_BUCKET, 'Key': file_key},
                                ExpiresIn=3600
                            )
                            
                            image_urls.append({
                                'figure': img_data['i'],
                                'url': url,
                                's3_key': file_key
                            })
                            
                        except Exception as e:
                            print(f"S3 upload error for figure {img_data['i']}: {e}")
                            result["debug_info"][f"s3_upload_error_fig{img_data['i']}"] = str(e)
                            result["debug_info"]["s3_fallback_message"] = "S3 upload failed, using base64 fallback"
                
                # 結果を返す
                result["structuredContent"]["stdout"] = clean_out
                
                if image_urls:
                    result["structuredContent"]["image_urls"] = image_urls
                    result["debug_info"]["s3_upload_success"] = True
                    result["debug_info"]["uploaded_count"] = len(image_urls)
                    result["debug_info"]["s3_bucket"] = S3_BUCKET
                
            except Exception as e:
                result["debug_info"]["image_parse_error"] = str(e)
        else:
            result["debug_info"]["images_found"] = 0
        
        return json.dumps(result, ensure_ascii=False)
    
    except Exception as e:
        # エラー時も適切なフォーマットで返す
        error_result = {
            "isError": True,
            "structuredContent": {
                "stdout": "",
                "stderr": f"Error executing code: {str(e)}",
                "exitCode": 1
            },
            "debug_info": {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "code_size": len(img_code)
            }
        }
        return json.dumps(error_result, ensure_ascii=False)

model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    params={"max_tokens": 4096, "temperature": 0.7},
    region="us-west-2"
)

agent = Agent(
    tools=[execute_python],
    system_prompt=SYSTEM_PROMPT,
    model=model
)

@app.entrypoint
async def code_interpreter_agent(payload: Dict[str, Any]) -> str:
    user_input = payload.get("prompt", "")
    
    response_text = ""
    tool_results = []
    
    async for event in agent.stream_async(user_input):
        if "data" in event:
            response_text += event["data"]
        # ツールの実行結果を収集
        elif "tool_result" in event:
            try:
                result = json.loads(event["tool_result"])
                if isinstance(result, dict) and "structuredContent" in result:
                    tool_results.append(result)
            except:
                pass
    
    # S3 URLsがある場合はレスポンスに含める
    image_urls = []
    for tool_result in tool_results:
        if "structuredContent" in tool_result and "image_urls" in tool_result["structuredContent"]:
            image_urls.extend(tool_result["structuredContent"]["image_urls"])
    
    if image_urls:
        response_text += "\n\n **Generated Visualizations (S3 URLs - Valid for 1 hour):**"
        for img_url_data in image_urls:
            response_text += f"\n **Figure {img_url_data['figure']}**: [View Graph]({img_url_data['url']})"
            response_text += f"\n   └── Direct Link: {img_url_data['url']}"
    
    return response_text

if __name__ == "__main__":
    app.run()