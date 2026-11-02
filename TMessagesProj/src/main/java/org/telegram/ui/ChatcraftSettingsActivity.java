package org.telegram.ui;

import android.content.Context;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;
import org.telegram.messenger.ChatcraftCore;
import org.telegram.messenger.ChatcraftUiIds;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;

import java.util.Locale;
import java.util.TreeSet;

public class ChatcraftSettingsActivity extends BaseFragment {
    private LinearLayout controls;
    private Context context;

    @Override
    public View createView(Context context) {
        this.context = context;
        actionBar.setTitle("Chatcraft");
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override
            public void onItemClick(int id) {
                if (id == -1) finishFragment();
            }
        });
        LinearLayout root = new LinearLayout(context);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        EditText search = new EditText(context);
        search.setSingleLine(true);
        search.setHint("Search settings / stable UI ID");
        root.addView(search);
        ScrollView scroll = new ScrollView(context);
        controls = new LinearLayout(context);
        controls.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(controls);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        search.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            public void onTextChanged(CharSequence s, int start, int before, int count) { refresh(s.toString()); }
            public void afterTextChanged(Editable s) {}
        });
        fragmentView = root;
        refresh("");
        return root;
    }

    private void refresh(String query) {
        controls.removeAllViews();
        try {
            JSONObject settings = ChatcraftCore.settings();
            String error = ChatcraftCore.error();
            TextView info = new TextView(context);
            info.setText(error == null ? "Shared across accounts. UI IDs cover only explicitly integrated native controls. Sponsored changes apply when reopening a chat." : "Settings error: " + error);
            info.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            controls.addView(info);
            String needle = query.toLowerCase(Locale.ROOT);
            option("Hide grouped chats in main list", "hide_grouped_chats", settings.optBoolean("hide_grouped_chats"), needle, false);
            option("Hide sponsored messages", "hide_sponsored", settings.optBoolean("hide_sponsored", true), needle, false);
            for (String id : ChatcraftUiIds.IDS) {
                option("Show " + id, id, ChatcraftCore.visible(id), needle, true);
            }
            android.widget.Button reset = new android.widget.Button(context);
            reset.setText("Restore defaults");
            controls.addView(reset);
            reset.setOnClickListener(view -> {
                try {
                    JSONObject defaults = ChatcraftCore.settings();
                    defaults.put("version", 1);
                    defaults.put("hide_grouped_chats", false);
                    defaults.put("read_first", false);
                    defaults.put("hide_sponsored", true);
                    defaults.put("hidden_ui_ids", new JSONArray());
                    ChatcraftCore.save(defaults);
                    refresh(query);
                } catch (Exception failure) {
                    Toast.makeText(context, failure.toString(), Toast.LENGTH_LONG).show();
                }
            });
        } catch (Exception error) {
            Toast.makeText(context, error.toString(), Toast.LENGTH_LONG).show();
        }
    }

    private void option(String label, String key, boolean checked, String query, boolean ui) {
        if (!(label + " " + key).toLowerCase(Locale.ROOT).contains(query)) return;
        CheckBox box = new CheckBox(context);
        box.setText(label);
        box.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        box.setChecked(checked);
        controls.addView(box);
        boolean[] restoring = {false};
        box.setOnCheckedChangeListener((button, value) -> {
            if (restoring[0]) return;
            try {
                JSONObject settings = ChatcraftCore.settings();
                if (ui) {
                    TreeSet<String> hidden = new TreeSet<>();
                    JSONArray ids = settings.getJSONArray("hidden_ui_ids");
                    for (int i = 0; i < ids.length(); i++) hidden.add(ids.getString(i));
                    if (value) hidden.remove(key); else hidden.add(key);
                    settings.put("hidden_ui_ids", new JSONArray(hidden));
                } else {
                    settings.put(key, value);
                }
                ChatcraftCore.save(settings);
            } catch (Exception error) {
                restoring[0] = true;
                button.setChecked(!value);
                restoring[0] = false;
                Toast.makeText(context, error.toString(), Toast.LENGTH_LONG).show();
            }
        });
    }
}
