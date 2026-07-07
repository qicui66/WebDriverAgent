"""Inject custom pasteboard endpoints into WDA FBCustomCommands.m

Adds two endpoints:
  POST /wda/setPasteboardText  {text: "..."}  — write text to system pasteboard
  GET  /wda/getPasteboardText                  — read current pasteboard content
"""
import sys

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'r') as f:
    content = f.read()

# 如果已注入，跳过
if 'handleSetPasteboardText' in content and 'handleGetPasteboardText' in content:
    print('Pasteboard endpoints already injected, skip')
    sys.exit(0)

print('Injecting pasteboard endpoints...')

# 路由注入
route_anchor = '    [[FBRoute POST:@"/wda/device/appearance"].withoutSession respondWithTarget:self action:@selector(handleSetDeviceAppearance:)],'

pasteboard_routes = (
    '    [[FBRoute POST:@"/wda/setPasteboardText"] respondWithTarget:self action:@selector(handleSetPasteboardText:)],\n'
    '    [[FBRoute GET:@"/wda/getPasteboardText"] respondWithTarget:self action:@selector(handleGetPasteboardText:)],'
)

if route_anchor in content:
    content = content.replace(route_anchor, route_anchor + '\n' + pasteboard_routes)
else:
    print('ERROR: Route anchor not found in FBCustomCommands.m')
    sys.exit(1)

# 方法注入
pasteboard_methods = r'''+ (id<FBResponsePayload>)handleSetPasteboardText:(FBRouteRequest *)request
{
  NSString *text = request.arguments[@"text"];
  if (nil == text || ![text isKindOfClass:[NSString class]]) {
    return FBResponseWithStatus([FBCommandStatus invalidArgumentErrorWithMessage:@"text must be a non-empty string" traceback:nil]);
  }
  // UIPasteboard MUST be accessed from the main thread
  __block BOOL success = NO;
  dispatch_sync(dispatch_get_main_queue(), ^{
    [[UIPasteboard generalPasteboard] setString:text];
    success = YES;
  });
  if (success) {
    return FBResponseWithOK();
  }
  return FBResponseWithStatus([FBCommandStatus unknownErrorWithMessage:@"Failed to set pasteboard" traceback:nil]);
}

+ (id<FBResponsePayload>)handleGetPasteboardText:(FBRouteRequest *)request
{
  __block NSString *text = nil;
  dispatch_sync(dispatch_get_main_queue(), ^{
    text = [[UIPasteboard generalPasteboard] string];
  });
  return FBResponseWithObject(text ?: @"");
}'''

content = content.replace('\n@end', '\n' + pasteboard_methods + '\n@end')

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'w') as f:
    f.write(content)

print('Pasteboard endpoints injected successfully!')
