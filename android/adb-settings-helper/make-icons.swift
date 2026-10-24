import AppKit

func save(_ path: String, size: NSSize, title: String, fontSize: CGFloat) {
    let image = NSImage(size: size)
    image.lockFocus()
    NSColor(calibratedRed: 0.12, green: 0.28, blue: 0.65, alpha: 1).setFill()
    NSRect(origin: .zero, size: size).fill()
    let attributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: fontSize, weight: .bold),
        .foregroundColor: NSColor.white
    ]
    let textSize = (title as NSString).size(withAttributes: attributes)
    let origin = NSPoint(x: (size.width - textSize.width) / 2,
                         y: (size.height - textSize.height) / 2)
    (title as NSString).draw(at: origin, withAttributes: attributes)
    image.unlockFocus()
    let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
    let png = bitmap.representation(using: .png, properties: [:])!
    try! png.write(to: URL(fileURLWithPath: path))
}

let directory = CommandLine.arguments[1]
save(directory + "/banner.png", size: NSSize(width: 320, height: 180),
     title: "开发者选项", fontSize: 32)
save(directory + "/icon.png", size: NSSize(width: 144, height: 144),
     title: "DEV", fontSize: 44)
