# iDS TT Video Marker ver 2.3

## 主な変更点

- ラベル付けしたフレーム一覧を表示する右のリストに逆順で表示するチェックボックスを追加
   - 最近つけたラベルが表示されるようにする暫定的機能

### 既知のバグ

- ステータスバー`MainStatusBar`のスタイルシートが効かない

### バージョン 2.1 の注意点

このバージョンからはもう`markdata`フォルダを開く必要はありません。
画面上のメニューバーの「Label」→「Export」で`markdata`フォルダの内容をzipファイルでエクスポートすることができます。
エクスポートしたzipファイルをMattermostのDMで送ってください。

### バージョン 2.X の注意点

バージョン 2.X はマークデータ（jsonファイル）構造の変更を含みます。
**バージョン 1.X から 2.X へアップデートするときは、不具合があった場合に備えて、古いバージョンの`markdata`
フォルダのjsonファイルは、消さずに別の場所に取っておいてください！**

旧バージョンのマークデータが json-version 1 で、このバージョンのマークデータが json-version 2 です。
バージョン 2.X で json-version 1 を読み込むと、自動的に json-version 2 へ変換します。

## 使い方

### インストール

1. GitHubの左上のブランチ（もしかしたら「master」と書いてあるところ）から`release/stable/<バージョン>`を選択する
    - 最新版を選んでください
2. GitHubの右上の「Code」から「Download ZIP」をクリックしてZIPファイルをダウンロードする
3. ダウンロードしたZIPファイルを展開する
4. 展開したフォルダの`run.bat`を実行する

### 動画の読み込み

1. 起動したアプリに動画をドラッグ＆ドロップする

### ラベルのつけ方

1. 下の操作方法を参考にしてフレームをラベルをつけるフレームを探す
    - 1フレーム進むキーを押し続けると動画を再生するようにフレームを送ることができる
2. 下の操作方法を参考にしてラベルを編集する
    - 右側のパネルのボタンを押しても編集可

**ラベルデータはすべて自動保存です。**終了するときはそのままウィンドウを閉じてください。

### ラベルデータの提出

1. メニューバーの「Label」→「Export」をクリックしてエクスポート先フォルダ選択画面を開く
2. エクスポート先のフォルダを選択する
    - 上書きしていいか聞かれた場合は前回エクスポートしたデータが残っているので適宜指示に従う
3. zipファイルがエクスポートされる
4. エクスポートしたzipファイルをMattermostのDMで提出する

## アップデート

1. 「インストール」と同じ手順で最新バージョンをインストールする。
    - **このとき旧バージョンを上書きしない！**
2. アプリを起動している場合はすべて閉じる
3. **ラベルデータを引き継ぐ【重要】**
    - 方法１：旧バージョンの`markdata`フォルダを、新バージョンの`run.bat`があるフォルダにコピーする。
    - 方法２（アップデート前バージョン2.1以上）：旧バージョンでエクスポート（「Label」→「Export」）した
      ラベルデータを、新バージョンでインポート（「Label」→「Import」）する。**インポートは動画を開く前に行う。**
4. 新バージョンを実行して旧バージョンで作業していた動画を開き、データが引き継がれていれば完了

## 操作方法

### 基本操作

|                 キー                 |             操作             |
|:----------------------------------:|:--------------------------:|
|              `A`/`D`               |      1フレーム前・1フレーム次へ進む      |
|        `Shift+A`/`Shift+D`         |      5フレーム前・5フレーム次へ進む      |
|         `Ctrl+A`/`Ctrl+D`          |        10秒前・10秒次へ進む        |
|   `Ctrl+Shift+A`/`Ctrl+Shift+D`    |     最初のフレーム・最後のフレームへ進む     |
|    `Q`/`E` <br>（`A`/`D`の１つ上のキー）    |       前のラベル/次のラベルへ進む       |
|   `1`, `2`, `3`, ... <br>（数字キー）    | ラベルをつける<br>もう一度押してラベルを削除する |
| `Z`, `X`, `C`, ... <br>（キーボードの下の列） | タグを追加する<br>もう一度押してタグを除去する  |

### 作業状況の保存

マークデータはすべて自動保存です。終了するときはそのままウィンドウを閉じればOK！
