import sys

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'r') as f:
    content = f.read()

# 如果已有完整注入（图片+视频），跳过
if 'handleSaveVideoToCameraRoll' in content and 'handleSaveImageToCameraRoll' in content:
    print('Already fully injected (image+video), skip')
    sys.exit(0)

# 移除旧的图片单注入（如果存在但不完整）
need_image = 'handleSaveImageToCameraRoll' not in content
need_video = 'handleSaveVideoToCameraRoll' not in content

print(f'Need image: {need_image}, Need video: {need_video}')

# 构建要添加的路由
new_routes = []
if need_image:
    new_routes.append('    [[FBRoute POST:@"/wda/saveImageToCameraRoll"] respondWithTarget:self action:@selector(handleSaveImageToCameraRoll:)],')
if need_video:
    new_routes.append('    [[FBRoute POST:@"/wda/saveVideoToCameraRoll"] respondWithTarget:self action:@selector(handleSaveVideoToCameraRoll:)],')

# 注入路由
old_route = '    [[FBRoute POST:@"/wda/device/appearance"].withoutSession respondWithTarget:self action:@selector(handleSetDeviceAppearance:)],'
content = content.replace(old_route, old_route + '\n' + '\n'.join(new_routes))

# 构建要添加的方法
new_methods = []
if need_image:
    new_methods.append("""+ (id<FBResponsePayload>)handleSaveImageToCameraRoll:(FBRouteRequest *)request
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
}""")

if need_video:
    new_methods.append("""+ (id<FBResponsePayload>)handleSaveVideoToCameraRoll:(FBRouteRequest *)request
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
}""")

# 注入方法（在 @end 前）
method_code = '\n\n' + '\n\n'.join(new_methods) + '\n'
content = content.replace('@end', method_code + '\n@end')

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'w') as f:
    f.write(content)

print(f'Injection done! Image: {need_image}, Video: {need_video}')
