/*
 * Copyright (C) 2010 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.android.apps.tag;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

/**
 * @author nnk@google.com (Nick Kralevich)
 */
public class TagListAdapter extends BaseAdapter {

    private Context context;

    TagListAdapter(Context context) {
        this.context = context;
    }

    private static final String[] listItems = {
            "Welcome! T2000 Festival",
            "Free songs by Hula 88",
            "Welcome to FreeBucks",
            "BooBox Movie Coupons"
    };

    @Override
    public int getCount() {
        return listItems.length;
    }

    @Override
    public String getItem(int position) {
        return listItems[position];
    }

    @Override
    public long getItemId(int position) {
        return position;
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        TextView tv = new TextView(context);
        tv.setText(getItem(position));
        return tv;
    }
}
