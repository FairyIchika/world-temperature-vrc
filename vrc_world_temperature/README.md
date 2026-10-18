# World City Temperature — VRChat

60都市の現在気温（Open-Meteoモデル推定値）を同一取得時点で単純平均し、VRChatのTextMeshProに表示します。

## 1. GitHubに公開する

1. 新しい**公開**GitHubリポジトリを作り、このフォルダ内のファイル（`.github`も含む）をルートにアップロードします。
2. リポジトリの **Settings → Actions → General → Workflow permissions** で、必要に応じて **Read and write permissions** を許可します（組織ポリシーにより不可の場合あり）。
3. **Actions → Update world temperature → Run workflow** で初回実行。成功後 `temperature.txt` が生成されます。
4. **Settings → Pages → Build and deployment → Deploy from a branch** を選び、`main` / `(root)` を選択して保存。
5. 数分後、`https://USERNAME.github.io/REPOSITORY/temperature.txt` に `19.6|60|2026-10-18 00:00 UTC` のような文字列が表示されれば配信側は完成です。

GitHub Actionsの15分周期は厳密な保証ではなく、遅延やスキップがありえます。無料プラン等の利用規約・制限を確認してください。API失敗時には以前のファイルを維持するため、表示時刻も必ず確認してください。

## 2. Unity / VRChat

1. VCC管理のUdonSharpワールドプロジェクトに `Assets/WorldTemperatureDisplay.cs` をコピー。
2. World Space Canvas を作成し、TextMeshPro - Text (UI) を2つ配置。気温表示とステータス表示にします。
3. 空のGameObjectに `WorldTemperatureDisplay` を追加。`Temperature Text` / `Status Text` にTMPを割り当て。
4. `Data Url` に公開した `https://USERNAME.github.io/REPOSITORY/temperature.txt` を設定。
5. `Refresh Seconds` は900（15分）を推奨。初期値も900です。
6. Unity Playだけでなく、VRChatのBuild & Testで実際のURL取得を確認。

**重要:** VRChatではユーザーの設定やワールドの信頼設定により外部URLの取得が制限されることがあります。URLの許可確認・Trusted URLs・ユーザーのUntrusted URLs設定など、実機環境で確認してください。全ユーザーが同じ表示を見られるとは限りません。

## 3. 仕様と注意

- 60都市すべての気温が揃った場合のみ更新し、欠測時は以前の結果を維持。
- 60都市の気温はAPI応答の「現在」推定値であり、世界全体の地表平均気温ではありません。
- 時刻はUTC。GitHub Actions実行時刻と各地点の気象モデルの有効時刻は完全には一致しない場合があります。
- 取得したファイルは公開データです。APIの商用利用条件とクレジット表記を確認してください。
- VRCStringDownloaderの利用はプラットフォーム・URL制限の影響を受けます。実際のVRChatクライアントで検証してください。
