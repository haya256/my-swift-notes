// 日本語で検索できるようにする(Just the Docs の lunr 検索の差し込み口)。
// テーマの検索インデックスを作る処理の中で、記事ごとに呼ばれる(this は lunr の Builder)。
// 最初の1回だけ、次のことを変える。
//   1. 区切り方:日本語(漢字・ひらがな・カタカナ)は2文字ずつ(バイグラム)に区切る。英数字は今まで通り単語ごと
//   2. 処理の流れ:英数字以外を消してしまう trimmer などを外す(日本語が消えるのを防ぐ)。
//      英語の語尾をそろえる stemmer も外す(前方一致の検索で、everyone → everyon のようなずれが起きて見つからなくなるため)
//   ひらがなはカタカナに、全角英数字は半角にそろえる(「ぶーすと」で「ブースト」、「ＭＢ」で「MB」が見つかる)。文字数は変わらない
// lunr.tokenizer も差しかえるので、検索ワードの側も同じ区切り方になる。
if (!this.__jaTokenizerInstalled) {
  this.__jaTokenizerInstalled = true;

  var JA = '\\p{sc=Han}\\p{sc=Hiragana}\\p{sc=Katakana}\\u30fc\\u3005';
  var TOKEN_RE = new RegExp('[' + JA + ']+|[^\\s\\p{P}\\p{S}' + JA + ']+', 'gu');
  var JA_RE = new RegExp('^[' + JA + ']', 'u');

  var jaTokenizer = function (obj, metadata) {
    if (obj === null || obj === undefined) {
      return [];
    }
    if (Array.isArray(obj)) {
      return obj.map(function (t) {
        return new lunr.Token(lunr.utils.asString(t).toLowerCase(), lunr.utils.clone(metadata));
      });
    }

    var str = obj.toString().replace(/[\u3041-\u3096]/g, function (c) {
      return String.fromCharCode(c.charCodeAt(0) + 0x60);
    }).replace(/[\uff01-\uff5e]/g, function (c) {
      return String.fromCharCode(c.charCodeAt(0) - 0xfee0);
    }).toLowerCase();
    var tokens = [];
    var m;
    TOKEN_RE.lastIndex = 0;
    while ((m = TOKEN_RE.exec(str)) !== null) {
      var word = m[0];
      var start = m.index;
      var pieces = [];
      if (JA_RE.test(word) && word.length > 1) {
        for (var i = 0; i + 1 < word.length; i++) {
          pieces.push([word.substr(i, 2), start + i]);
        }
      } else {
        pieces.push([word, start]);
      }
      for (var j = 0; j < pieces.length; j++) {
        var meta = lunr.utils.clone(metadata) || {};
        meta.position = [pieces[j][1], pieces[j][0].length];
        meta.index = tokens.length;
        tokens.push(new lunr.Token(pieces[j][0], meta));
      }
    }
    return tokens;
  };
  jaTokenizer.separator = lunr.tokenizer.separator;

  lunr.tokenizer = jaTokenizer;
  this.tokenizer = jaTokenizer;

  this.pipeline.reset();
  this.searchPipeline.reset();

  // 3. 検索ワードの「2文字ずつ」がすべて含まれるページだけを出す(どれか1つでよい、だと関係ないページが大量に出る)。
  //    テーマは「完全一致(加点用)」と「前方一致」の2通りで検索する。前方一致の方だけを必須にする
  //    (1文字だけの検索ワードは前方一致でしか当たらないため)。
  var originalClause = lunr.Query.prototype.clause;
  lunr.Query.prototype.clause = function (clause) {
    if ((clause.wildcard & lunr.Query.wildcard.TRAILING) && clause.presence === undefined) {
      clause.presence = lunr.Query.presence.REQUIRED;
    }
    return originalClause.call(this, clause);
  };

  // 4. 検索結果のハイライト位置の重なりをまとめる。
  //    2文字ずつのかたまりは1文字ずつ重なる(「ブー」「ース」「スト」)。テーマのハイライト処理は重なりを想定しておらず、
  //    そのままだと「ブーースト」のように文字が崩れる。項目(title / content)ごとに、全部の語の位置を
  //    つなげた区間にまとめ、最初の語にだけ持たせる(テーマはすべての語の位置を集めて使うので、結果は同じになる)。
  //    lunr は索引のデータをそのまま渡してくるので、中身は書きかえず、新しいオブジェクトに置きかえる
  //    (書きかえると索引が壊れ、次の検索のハイライトがずれる)。
  var withPosition = function (fieldMetadata, positions) {
    var copy = {};
    Object.keys(fieldMetadata).forEach(function (key) {
      copy[key] = fieldMetadata[key];
    });
    copy.position = positions;
    return copy;
  };
  var originalQuery = lunr.Index.prototype.query;
  lunr.Index.prototype.query = function (fn) {
    var results = originalQuery.call(this, fn);
    results.forEach(function (result) {
      var metadata = result.matchData.metadata;
      var merged = {};
      var owner = {};
      Object.keys(metadata).forEach(function (term) {
        Object.keys(metadata[term]).forEach(function (field) {
          var positions = metadata[term][field].position;
          if (!positions) {
            return;
          }
          merged[field] = (merged[field] || []).concat(positions);
          if (owner[field] === undefined) {
            owner[field] = term;
          } else {
            metadata[term][field] = withPosition(metadata[term][field], []);
          }
        });
      });
      Object.keys(merged).forEach(function (field) {
        var list = merged[field].slice().sort(function (a, b) { return a[0] - b[0]; });
        var out = [];
        list.forEach(function (p) {
          var last = out[out.length - 1];
          if (last && p[0] <= last[0] + last[1]) {
            last[1] = Math.max(last[1], p[0] + p[1] - last[0]);
          } else {
            out.push([p[0], p[1]]);
          }
        });
        metadata[owner[field]][field] = withPosition(metadata[owner[field]][field], out);
      });
    });
    return results;
  };
}
