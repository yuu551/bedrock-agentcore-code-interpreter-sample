# Code Interpreter Agent サンプル

このフォルダには、Amazon Bedrock AgentCore Code Interpreterを使用するStrands Agentの実装例、およびテスト用のスクリプトが含まれています。

## ファイル構成

```
sample_code_interpreter/
├── agent.py                 # Code Interpreterを使用するStrands Agent実装
├── create_iam_role.py      # IAMロール作成スクリプト
├── deploy_runtime.py       # AgentCore Runtimeデプロイスクリプト
├── test_invoke.py          # デプロイ後の動作テストスクリプト
├── requirements.txt        # Python依存関係
└── README.md              # このファイル
```

## セットアップ手順

### 1. 仮想環境の作成と依存関係インストール

```bash
# 仮想環境作成
python -m venv code-interpreter-env
source code-interpreter-env/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. IAMロール作成

```bash
python create_iam_role.py
```

実行結果に表示されるRole ARNをメモしてください。

### 3. デプロイスクリプトの設定

`deploy_runtime.py` の `runtime_role_arn` を実際の値に置き換えます：

```python
# 変更前
runtime_role_arn = "arn:aws:iam::YOUR_ACCOUNT:role/CodeInterpreterRuntimeRole-XXXXXXXXXX"

# 変更後（例）
runtime_role_arn = "arn:aws:iam::123456789012:role/CodeInterpreterRuntimeRole-1234567890"
```

### 4. Runtimeデプロイ

```bash
python deploy_runtime.py
```

実行結果に表示されるAgent ARNをメモしてください。

### 5. テストスクリプトの設定

`test_invoke.py` の `agent_arn` を実際の値に置き換えます。

```python
# 変更前
agent_arn = "arn:aws:bedrock-agentcore:us-west-2:YOUR_ACCOUNT:agent-runtime/code-interpreter-agent-xxxxx"

# 変更後（例）
agent_arn = "arn:aws:bedrock-agentcore:us-west-2:123456789012:agent-runtime/code-interpreter-agent-abcdef12345"
```

### 6. 動作テスト

```bash
# テスト
python test_invoke.py
```

## 前提条件

- AWS CLI設定済み
- Python 3.1以上
- us-west-2リージョンでのCode Interpreter利用権限
- anthropic.claude-3-5-sonnet-20241022-v2:0へのアクセス権限