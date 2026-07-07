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
  [[UIPasteboard generalPasteboard] setString:text];
  return FBResponseWithOK();
}

+ (id<FBResponsePayload>)handleGetPasteboardText:(FBRouteRequest *)request
{
  NSString *text = [[UIPasteboard generalPasteboard] string];
  return FBResponseWithObject(text ?: @"");
}'''

content = content.replace('\n@end', '\n' + pasteboard_methods + '\n@end')

with open('WebDriverAgentLib/Commands/FBCustomCommands.m', 'w') as f:
    f.write(content)

print('Pasteboard endpoints injected successfully!')
