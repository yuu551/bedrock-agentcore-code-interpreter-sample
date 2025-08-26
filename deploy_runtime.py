#!/usr/bin/env python3
"""
Code Interpreter Agent をAgentCore Runtimeとしてデプロイ
"""

from bedrock_agentcore_starter_toolkit import Runtime

def deploy_code_interpreter_runtime():
    """
    Code Interpreter Agentをデプロイ
    """
    
    print("🚀 Code Interpreter Agent のデプロイを開始...")
    
    # 先ほど作成したIAMロールARNを設定
    # 実際の値に置き換えてください
    runtime_role_arn = "arn:aws:iam::<YOUR_ACCOUNT_ID>:role/CodeInterpreterRuntimeRole-REPLACE_ME"
    
    # 上記のruntime_role_arnを実際の値に置き換えてから実行してください！
    if "YOUR_ACCOUNT" in runtime_role_arn:
        print("エラー: runtime_role_arnを実際の値に置き換えてください")
        print("   create_iam_role.pyの実行結果から取得したARNを設定してください")
        return None
    
    # Runtimeの設定（認証なし）
    runtime = Runtime()
    
    response = runtime.configure(
        entrypoint="agent.py",  # Code Interpreterエージェントのファイル名
        execution_role=runtime_role_arn,
        auto_create_ecr=True,  # ECRリポジトリを自動作成
        requirements_file="requirements.txt",
        region="us-west-2",
        agent_name="code_interpreter_agent_2",
        # 認証設定なし（開発環境用）
    )
    
    print("✅ Runtime設定完了！デプロイ中...")
    
    # デプロイ実行
    launch_result = runtime.launch()
    
    print(f"✅ Code Interpreter Agent デプロイ完了！")
    print(f"   Agent ARN: {launch_result.agent_arn}")
    print(f"   注意: このRuntimeは認証なしで動作します（開発環境用）")
    print("\n📝 メモ: Agent ARNをtest_invoke.pyのagent_arn変数に設定してください")
    
    return launch_result

if __name__ == "__main__":
    deploy_code_interpreter_runtime()