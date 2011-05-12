#ifndef GLES_V2_VALIDATE_H
#define GLES_V2_VALIDATE_H

/*
* Copyright (C) 2011 The Android Open Source Project
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

#include <GLES2/gl2.h>
#include <GLcommon/GLESvalidate.h>

struct GLESv2Validate:public GLESvalidate{
static bool blendEquationMode(GLenum mode);
static bool blendSrc(GLenum s);
static bool blendDst(GLenum d);
static bool textureTarget(GLenum target);
static bool textureTargetEx(GLenum target);
static bool textureParams(GLenum param);
static bool hintTargetMode(GLenum target,GLenum mode);
static bool capability(GLenum cap);
static bool pixelStoreParam(GLenum param);
static bool readPixelFrmt(GLenum format);
static bool framebufferTarget(GLenum target);
static bool framebufferAttachment(GLenum attachment);
static bool framebufferAttachmentParams(GLenum pname);
static bool renderbufferTarget(GLenum target);
static bool renderbufferParams(GLenum pname);

};

#endif
