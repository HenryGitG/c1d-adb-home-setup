package com.henry.c1d.devsettings;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.UserManager;
import android.provider.Settings;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/** Owner-operated shortcuts to settings screens already present in the C1D firmware. */
public final class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showMenu("请选择要打开的系统页面。");
    }

    private void showMenu(String status) {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER);
        panel.setPadding(40, 40, 40, 40);
        panel.setBackgroundColor(Color.rgb(20, 25, 34));

        UserManager users = (UserManager) getSystemService(USER_SERVICE);
        boolean restricted = users != null
                && users.hasUserRestriction(UserManager.DISALLOW_DEBUGGING_FEATURES);

        TextView message = new TextView(this);
        message.setText(status
                + "\n\nAndroid " + Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")"
                + "\n系统调试限制：" + (restricted ? "已启用" : "未检测到"));
        message.setTextColor(Color.WHITE);
        message.setTextSize(24);
        message.setGravity(Gravity.CENTER);
        panel.addView(message);

        addButton(panel, "打开 TV 开发者选项", this::openTvDeveloperSettings);
        addButton(panel, "打开 Android 开发者选项", this::openAndroidDeveloperSettings);
        addButton(panel, "打开画面缩放（C1D 调试入口）", this::openScreenSize);
        addButton(panel, "显示远程协助连接信息", this::showRemoteAssistanceInfo);
        addButton(panel, "打开系统信息", this::openAboutSettings);

        setContentView(panel);
        panel.getChildAt(1).requestFocus();
    }

    private void addButton(LinearLayout panel, String label, Runnable action) {
        Button button = new Button(this);
        button.setText(label);
        button.setOnClickListener(view -> action.run());
        panel.addView(button);
    }

    private void openTvDeveloperSettings() {
        Intent intent = new Intent();
        intent.setClassName("com.android.tv.settings",
                "com.android.tv.settings.system.development.DevelopmentActivity");
        open(intent, "TV 开发者选项");
    }

    private void openAndroidDeveloperSettings() {
        open(new Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS), "Android 开发者选项");
    }

    private void openScreenSize() {
        try {
            Intent intent = new Intent("obe.action.SCREEN_SIZE");
            intent.setClassName("com.obe.settings",
                    "com.obe.settings.projector.ProjectorSettingsReceiver");
            sendBroadcast(intent);
            showMenu("已请求打开画面缩放。进入该页面后，按文档中的设备专用步骤操作。");
        } catch (RuntimeException error) {
            showMenu("无法打开画面缩放：" + error.getClass().getSimpleName());
        }
    }

    private void openAboutSettings() {
        Intent tvAbout = new Intent();
        tvAbout.setClassName("com.android.tv.settings",
                "com.android.tv.settings.about.AboutActivity");
        try {
            startActivity(tvAbout);
        } catch (RuntimeException ignored) {
            open(new Intent(Settings.ACTION_DEVICE_INFO_SETTINGS), "系统信息");
        }
    }

    private void showRemoteAssistanceInfo() {
        String serial = readProperty("ro.serialno");
        if (serial.isEmpty()) serial = readProperty("ro.boot.serialno");
        String route = readProperty("persist.obe.REMOTE_DEBUG_URL");
        showMenu("仅在你自己的设备上使用，以下信息不要发布："
                + "\n\ndeviceSerial：" + (serial.isEmpty() ? "未读取到" : serial)
                + "\nremoteDebugUrl：" + (route.isEmpty() ? "未读取到" : route));
    }

    private String readProperty(String name) {
        try {
            Process process = new ProcessBuilder("getprop", name).start();
            try (BufferedReader output = new BufferedReader(new InputStreamReader(
                    process.getInputStream(), StandardCharsets.UTF_8))) {
                String value = output.readLine();
                return value == null ? "" : value.trim();
            } finally {
                process.destroy();
            }
        } catch (Exception ignored) {
            return "";
        }
    }

    private void open(Intent intent, String name) {
        try {
            startActivity(intent);
        } catch (RuntimeException error) {
            showMenu("无法打开" + name + "：" + error.getClass().getSimpleName());
        }
    }
}
