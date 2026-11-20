# このリポジトリについて(Claude Code 向け)

このリポジトリは、Swiftの知識ベースです。テンプレート `haya256/my-notes-template` から作った **notes** です。

- 質問に答えるときは、README.md の「AIへの指示」に従ってください。
- 記事を書く・直す、`notes.py` を使う、しくみについて判断する前に、**KB_GUIDE.md** を読んでください。
- **共通の部分(`kb-engine.json` に載っているファイル。`notes.py`、`_layouts/`、`_includes/`、`KB_GUIDE.md` など)は、このリポジトリで直さないでください。**
  直したくなったら、テンプレート `haya256/my-notes-template` の方を直してから、ここで `python3 notes.py update` を実行して取りこみます(KB_GUIDE.md の「共通の部分を直したくなったら」)。
- README の `<!-- kb:...:start -->` などで囲まれた部分、目次、`_config.yml` は `python3 notes.py sync` が作ります。手で直さないでください。
