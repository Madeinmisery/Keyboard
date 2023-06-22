package com.example.android.aconfig.demo.activity;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

import com.android.aconfig.test.utils.AconfigFlagRules;

@RunWith(JUnit4.class)
public final class ContentProviderTests {

    @Test
    public void testFlag() {
        assertFalse(Flags.appendContent());
    }
}