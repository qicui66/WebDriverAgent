import sys

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'r') as f:
    content = f.read()

# 检查是否已经注入过
if 'handleSaveImageToCameraRoll' in content:
    print('Already injected, skip')
    sys.exit(0)

# 注入路由注册（在 handleSetDeviceAppearance 后面）
route_line = '    [[FBRoute POST:@"/wda/saveImageToCameraRoll"] respondWithTarget:self action:@selector(handleSaveImageToCameraRoll:)],'
old_route = '    [[FBRoute POST:@"/wda/device/appearance"].withoutSession respondWithTarget:self action:@selector(handleSetDeviceAppearance:)],'
content = content.replace(old_route, old_route + '\n' + route_line)

# 注入方法实现（在 @end 前面）
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
"""
content = content.replace('@end', method_code + '\n@end')

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'w') as f:
    f.write(content)

count = content.count('handleSaveImageToCameraRoll')
print('Injection done! Found {} occurrence(s)'.format(count))
