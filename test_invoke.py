"""
デプロイしたCode Interpreter Agentを呼び出すテストスクリプト
"""
import boto3
import json
def invoke_code_interpreter_agent():
    """デプロイしたエージェントを呼び出し"""
    
    # デプロイ時に取得したAgent ARNを設定
    agent_arn = "arn:aws:bedrock-agentcore:us-west-2:<YOUR_ACCOUNT_ID>:runtime/REPLACE_ME_AGENT_ID"
    
    # 上記のagent_arnを実際の値に置き換えてから実行してください！
    if "YOUR_ACCOUNT" in agent_arn:
        print("❌ エラー: agent_arnを実際の値に置き換えてください")
        print("   deploy_runtime.pyの実行結果から取得したAgent ARNを設定してください")
        return None
    
    client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    # Test queries in English
    queries = [
        """Analyze the following sales data:
    - Product A: [100, 120, 95, 140, 160, 180, 200]
    - Product B: [80, 85, 90, 95, 100, 105, 110]
    - Product C: [200, 180, 220, 190, 240, 260, 280]
    Please visualize the sales trends and calculate growth rates."""
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"テスト {i}: {query}")
        print(f"{'='*60}")
        
        payload = json.dumps({
            "prompt": query
        }).encode('utf-8')
        
        try:
            response = client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                qualifier="DEFAULT",
                payload=payload,
                contentType='application/json',
                accept='application/json'
            )
            
            # レスポンスの処理
            if response.get('contentType') == 'application/json':
                content = []
                for chunk in response.get('response', []):
                    content.append(chunk.decode('utf-8'))
                
                try:
                    
                    result = json.loads(''.join(content))
                    print("エージェント応答:")
                    print(result)
                        
                except json.JSONDecodeError:
                    print("📄 Raw応答:")
                    raw_content = ''.join(content)
                    print(raw_content)
                    
            else:
                print(f"予期しないContent-Type: {response.get('contentType')}")
                print(f"レスポンス: {response}")
            
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    
    invoke_code_interpreter_agent()