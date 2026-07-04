package com.downtube.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.Context;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.text.InputType;
import android.webkit.DownloadListener;
import android.webkit.JsResult;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.Toast;

/** DownTube 서버(웹 앱)를 감싸는 WebView 앱. 파일 다운로드는 안드로이드 DownloadManager로 저장한다. */
public class MainActivity extends Activity {
    /** 기본 접속 주소 — 고정 Cloudflare 주소. 첫 실행 시 자동으로 이 주소에 접속한다. */
    private static final String DEFAULT_BASE = "https://downtube.mooja4870.workers.dev";

    private WebView web;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("downtube", MODE_PRIVATE);

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView v, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) {
                    askServer("서버에 연결할 수 없습니다. Mac에서 run.sh가 실행 중인지, 주소가 맞는지 확인해 주세요.");
                }
            }
        });

        // WebChromeClient에서 JS confirm() 및 alert()를 네이티브 대화상자로 구현하여
        // 모든 기기에서 확인 및 알림창이 정상적으로 동작하도록 보장한다.
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onJsConfirm(WebView view, String url, String message, final JsResult result) {
                new AlertDialog.Builder(MainActivity.this)
                        .setTitle("DownTube")
                        .setMessage(message)
                        .setPositiveButton(android.R.string.ok, new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface dialog, int which) {
                                result.confirm();
                            }
                        })
                        .setNegativeButton(android.R.string.cancel, new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface dialog, int which) {
                                result.cancel();
                            }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            @Override
                            public void onCancel(DialogInterface dialog) {
                                result.cancel();
                            }
                        })
                        .setCancelable(false)
                        .show();
                return true;
            }

            @Override
            public boolean onJsAlert(WebView view, String url, String message, final JsResult result) {
                new AlertDialog.Builder(MainActivity.this)
                        .setTitle("DownTube")
                        .setMessage(message)
                        .setPositiveButton(android.R.string.ok, new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface dialog, int which) {
                                result.confirm();
                            }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            @Override
                            public void onCancel(DialogInterface dialog) {
                                result.confirm();
                            }
                        })
                        .setCancelable(false)
                        .show();
                return true;
            }
        });

        web.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition,
                                        String mimeType, long contentLength) {
                try {
                    // URLUtil.guessFileName은 mime이 octet-stream이면 확장자를 .bin으로 바꿔버리므로
                    // Content-Disposition과 URL 경로에서 직접 파일명을 추출한다.
                    String name = fileNameFrom(url, contentDisposition);
                    DownloadManager.Request r = new DownloadManager.Request(Uri.parse(url));
                    if (mimeType != null && !mimeType.isEmpty()) r.setMimeType(mimeType);
                    r.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                    r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
                    ((DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE)).enqueue(r);
                    Toast.makeText(MainActivity.this, name + " 저장 시작", Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    Toast.makeText(MainActivity.this, "저장 실패: " + e.getMessage(), Toast.LENGTH_LONG).show();
                }
            }
        });

        setContentView(web);

        // 저장된 주소가 있으면 그것을, 없으면 기본 고정 주소로 곧바로 접속 (입력 단계 생략)
        web.loadUrl(prefs.getString("base", DEFAULT_BASE));
    }

    /** Content-Disposition의 filename 항목 → URL 경로 순으로 파일명 추출 */
    private static String fileNameFrom(String url, String contentDisposition) {
        try {
            if (contentDisposition != null) {
                java.util.regex.Matcher m = java.util.regex.Pattern
                        .compile("filename\\*=(?:utf-8|UTF-8)''([^;]+)").matcher(contentDisposition);
                if (m.find()) return java.net.URLDecoder.decode(m.group(1).trim(), "UTF-8");
                m = java.util.regex.Pattern
                        .compile("filename=\"?([^\";]+)\"?").matcher(contentDisposition);
                if (m.find()) return m.group(1).trim();
            }
            String seg = Uri.parse(url).getLastPathSegment();
            if (seg != null && !seg.isEmpty()) return seg;
        } catch (Exception ignored) {
        }
        return "download";
    }

    /** 서버 주소 입력/변경 대화상자 */
    private void askServer(String message) {
        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        input.setHint("예: http://172.30.1.25:8756");
        input.setText(prefs.getString("base", DEFAULT_BASE));

        new AlertDialog.Builder(this)
                .setTitle("DownTube 서버 주소")
                .setMessage(message)
                .setView(input)
                .setCancelable(false)
                .setPositiveButton("연결", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        String url = input.getText().toString().trim();
                        if (url.isEmpty()) {
                            askServer("주소를 입력해 주세요.");
                            return;
                        }
                        if (!url.startsWith("http://") && !url.startsWith("https://")) {
                            url = "http://" + url;
                        }
                        prefs.edit().putString("base", url).apply();
                        web.loadUrl(url);
                    }
                })
                .show();
    }

    /** 뒤로가기: 웹 히스토리가 있으면 뒤로, 최상위면 서버 주소 변경 대화상자 */
    @Override
    public void onBackPressed() {
        if (web.canGoBack()) {
            web.goBack();
        } else {
            askServer("서버 주소를 변경하려면 새 주소를 입력하고, 계속 사용하려면 그대로 '연결'을 누르세요.");
        }
    }
}
