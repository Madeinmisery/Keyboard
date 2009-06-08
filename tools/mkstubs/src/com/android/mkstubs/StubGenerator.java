/*
 * Copyright (C) 2009 The Android Open Source Project
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

package com.android.mkstubs;

import com.android.mkstubs.stubber.ClassStubber;

import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.ClassWriter;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.Map.Entry;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;

/**
 * 
 */
class StubGenerator {

    /**
     * Generate source for the stubbed classes, mostly for debug purposes.
     * @throws IOException 
     */
    public void generateStubbedJar(File destJar,
            Map<String, ClassReader> classes,
            List<String> exclusions) throws IOException {

        TreeMap<String, byte[]> all = new TreeMap<String, byte[]>();

        for (Entry<String, ClassReader> entry : classes.entrySet()) {
            ClassReader cr = entry.getValue();
            
            byte[] b = visitClassStubber(cr, exclusions);
            String name = classNameToEntryPath(cr.getClassName());
            all.put(name, b);
        }

        createJar(new FileOutputStream(destJar), all);

        System.out.println(String.format("Wrote %s", destJar.getPath()));
    }

    /**
     * Utility method that converts a fully qualified java name into a JAR entry path
     * e.g. for the input "android.view.View" it returns "android/view/View.class"
     */
    String classNameToEntryPath(String className) {
        return className.replaceAll("\\.", "/").concat(".class");
    }

    /**
     * Writes the JAR file.
     * 
     * @param outStream The file output stream were to write the JAR. 
     * @param all The map of all classes to output.
     * @throws IOException if an I/O error has occurred
     */
    void createJar(FileOutputStream outStream, Map<String,byte[]> all) throws IOException {
        JarOutputStream jar = new JarOutputStream(outStream);
        for (Entry<String, byte[]> entry : all.entrySet()) {
            String name = entry.getKey();
            JarEntry jar_entry = new JarEntry(name);
            jar.putNextEntry(jar_entry);
            jar.write(entry.getValue());
            jar.closeEntry();
        }
        jar.flush();
        jar.close();
    }
    
    byte[] visitClassStubber(ClassReader cr, List<String> exclusions) {
        System.out.println("Stub " + cr.getClassName());

        // Rewrite the new class from scratch, without reusing the constant pool from the
        // original class reader.
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS);

        ClassVisitor stubWriter = new ClassStubber(cw);
        ClassVisitor filter = new FilterClassAdapter(stubWriter, exclusions);
        cr.accept(filter, 0 /*flags*/);
        return cw.toByteArray();
    }
}
