import AppKit
import Foundation

enum InspectionFailure: Error, CustomStringConvertible {
    case invalid(String)
    var description: String {
        switch self { case .invalid(let message): message }
    }
}

func inspect(bundleURL: URL?, name: String, fullColor: Bool = false) throws -> [String: Any] {
    if bundleURL == nil, name.hasPrefix("NSTouchBar") {
        throw InspectionFailure.invalid("Touch Bar-only artwork is not an ordinary menu fallback.")
    }
    let candidate = bundleURL.flatMap { Bundle(url: $0)?.image(forResource: NSImage.Name(name)) }
        ?? (bundleURL == nil ? NSImage(named: NSImage.Name(name)) : nil)
    guard let source = candidate else {
        throw InspectionFailure.invalid("The named image is missing from the bundle.")
    }
    let image = fullColor ? (source.copy() as? NSImage ?? source) : source
    if fullColor { image.size = NSSize(width: 16, height: 16) }
    guard image.isTemplate != fullColor else {
        throw InspectionFailure.invalid(fullColor ? "Full-color artwork must not use template rendering." : "The bundled image is not marked as a template.")
    }
    guard image.size.width > 0, image.size.height > 0,
          image.size.width <= 24, image.size.height <= 24 else {
        throw InspectionFailure.invalid("Use menu-sized artwork with a logical size of at most 24 points.")
    }
    let archive = try NSKeyedArchiver.archivedData(withRootObject: image, requiringSecureCoding: true)
    guard let restored = try NSKeyedUnarchiver.unarchivedObject(ofClass: NSImage.self, from: archive),
          restored.isTemplate == image.isTemplate else {
        throw InspectionFailure.invalid("The rendering intent did not survive secure archiving.")
    }
    if bundleURL == nil {
        guard candidate?.name() == name, restored.name() == name else {
            throw InspectionFailure.invalid("The system template name did not survive secure archiving.")
        }
        return ["image": name, "isTemplate": true, "transport": "system-name",
                "logicalWidth": image.size.width, "logicalHeight": image.size.height,
                "archivePreservesTemplate": true, "archivePreservesSystemName": true,
                "finderAppearanceVerified": false]
    }
    guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        throw InspectionFailure.invalid("The template artwork could not be decoded.")
    }
    let bitmap = NSBitmapImageRep(cgImage: cgImage)
    var visible = 0
    var transparent = 0
    var colored = 0
    for y in 0..<bitmap.pixelsHigh {
        for x in 0..<bitmap.pixelsWide {
            guard let color = bitmap.colorAt(x: x, y: y)?.usingColorSpace(.sRGB) else {
                throw InspectionFailure.invalid("The template color space could not be read.")
            }
            if color.alphaComponent < 0.02 { transparent += 1; continue }
            visible += 1
            if max(color.redComponent, color.greenComponent, color.blueComponent)
                - min(color.redComponent, color.greenComponent, color.blueComponent) > 0.06 { colored += 1 }
            if !fullColor && colored > 0 {
                throw InspectionFailure.invalid("Template artwork must be monochrome with transparency.")
            }
        }
    }
    guard visible > 0, fullColor || transparent > 0 else {
        throw InspectionFailure.invalid("The template must contain a visible mask and a transparent background.")
    }
    return ["image": name, "isTemplate": image.isTemplate, "resourceDecodable": true,
            "renderingIntent": fullColor ? "full-color" : "template",
            "transport": fullColor ? "full-color-resource" : "embedded-resource",
            "logicalWidth": image.size.width, "logicalHeight": image.size.height,
            "visiblePixels": visible, "transparentPixels": transparent,
            "coloredPixels": colored, "archivePreservesRenderingIntent": true, "finderAppearanceVerified": false]
}

guard (3...4).contains(CommandLine.arguments.count),
      CommandLine.arguments.count == 3 || (CommandLine.arguments[3] == "--full-color" && CommandLine.arguments[1] != "--system-image") else {
    fputs("Usage: swift inspect_menu_icon.swift <bundle|--system-image> <image-name> [--full-color]\n", stderr)
    exit(64)
}
do {
    let path = CommandLine.arguments[1]
    let report = try inspect(bundleURL: path == "--system-image" ? nil : URL(fileURLWithPath: path),
                             name: CommandLine.arguments[2], fullColor: CommandLine.arguments.count == 4)
    let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    print(String(decoding: data, as: UTF8.self))
} catch {
    fputs("FAIL: \(error)\n", stderr)
    exit(1)
}
