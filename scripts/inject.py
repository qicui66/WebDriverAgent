import sys

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'r') as f:
    content = f.read()

if 'handleSaveImageToCameraRoll' in content:
    print('Already injected, skip')
    sys.exit(0)

# === 注入路由（图片 + 视频）===
route_image = '    [[FBRoute POST:@"/wda/saveImageToCameraRoll"] respondWithTarget:self action:@selector(handleSaveImageToCameraRoll:)],'
route_video = '    [[FBRoute POST:@"/wda/saveVideoToCameraRoll"] respondWithTarget:self action:@selector(handleSaveVideoToCameraRoll:)],'
old_route = '    [[FBRoute POST:@"/wda/device/appearance"].withoutSession respondWithTarget:self action:@selector(handleSetDeviceAppearance:)],'
content = content.replace(old_route, old_route + '\n' + route_image + '\n' + route_video)

# === 注入方法实现 ===
method_code = """\
+ (id<FBResponsePayload>)handleSaveImageToCameraRoll:(FBRouteRequest *)request
{
#if TARGET_OS_TV
  return FBResponseWithStatus([FBCommandStatus unsupportedOperationErrorWithMessage:@"unsupported" traceback:nil]);
#else
  NSString *imageDataBase64 = request.arguments[@"imageData"];
  if (nil == imageDataBase64) {
    return FBResponseWithStatus([FBCommandStatus invalidArgumentErrorWithMessage:@"imageData must be provided" traceback:nil]);
  }
  NSData *imageData = [[NSData alloc] initWithBase64EncodedString:imageDataBase64 options:NSDataBase64DecodingIgnoreUnknownCharacters];
  if (nil == imageData) {
    return FBResponseWithStatus([FBCommandStatus invalidArgumentErrorWithMessage:@"Cannot decode imageData" traceback:nil]);
  }
  UIImage *image = [UIImage imageWithData:imageData];
  if (nil == image) {
    return FBResponseWithStatus([FBCommandStatus invalidArgumentErrorWithMessage:@"Cannot create image from data" traceback:nil]);
  }
  UIImageWriteToSavedPhotosAlbum(image, nil, nil, nil);
  return FBResponseWithOK();
#endif
}

+ (id<FBResponsePayload>)handleSaveVideoToCameraRoll:(FBRouteRequest *)request
{
#if TARGET_OS_TV
  return FBResponseWithStatus([FBCommandStatus unsupportedOperationErrorWithMessage:@"unsupported" traceback:nil]);
#else
  NSString *videoDataBase64 = request.arguments[@"videoData"];
  if (nil == videoDataBase64) {
    return FBResponseWithStatus([FBCommandStatus invalidArgumentErrorWithMessage:@"videoData must be provided" traceback:nil]);
  }
  NSData *videoData = [[NSData alloc] initWithBase64EncodedString:videoDataBase64 options:NSDataBase64DecodingIgnoreUnknownCharacters];
  if (nil == videoData) {
    return FBResponseWithStatus([FBCommandStatus invalidArgumentErrorWithMessage:@"Cannot decode videoData" traceback:nil]);
  }
  NSString *fileName = request.arguments[@"fileName"] ?: @"wda_video.mp4";
  NSString *tempPath = [NSTemporaryDirectory() stringByAppendingPathComponent:fileName];
  [videoData writeToFile:tempPath atomically:YES];
  UISaveVideoAtPathToSavedPhotosAlbum(tempPath, nil, nil, nil);
  return FBResponseWithOK();
#endif
}
"""
content = content.replace('@end', method_code + '\n@end')

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'w') as f:
    f.write(content)

print('Injection done! Image + Video + CameraRoll API')
