import SwiftUI

/// Cross-device sync, pairing and app-password management.
struct DevicesView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var devices: [JSON] = []
    @State private var deviceTokens: [JSON] = []
    @State private var pairing: JSON?
    @State private var claimCode = ""
    @State private var renaming: JSON?
    @State private var renameText = ""

    var body: some View {
        NavigationStack {
            List {
                Section("This device") {
                    LabeledContent("Name", value: app.deviceName)
                    LabeledContent("ID", value: String(app.deviceHash.prefix(8)))
                    Button("Use this device as the active speaker") {
                        if let current = devices.first(where: { $0["device_hash"]?.string == app.deviceHash }) {
                            Task { await activate(current.trackID) }
                        } else {
                            app.show("Play something first so this device is registered")
                        }
                    }
                }

                Section("Registered devices") {
                    if devices.isEmpty {
                        StateView(text: "No devices yet", icon: "monitor")
                    }
                    ForEach(devices, id: \.trackID) { device in
                        HStack {
                            LucideIcon(name: device["is_active"]?.bool == true ? "volume-2" : "volume-1",
                                       size: 18,
                                       color: device["is_active"]?.bool == true ? tokens.accent : tokens.dim)
                            VStack(alignment: .leading) {
                                Text(device["name"]?.string ?? "Unknown device")
                                Text(device["track_title"]?.string ?? "Idle")
                                    .font(.caption).foregroundStyle(tokens.dim)
                            }
                            Spacer()
                            if device["is_active"]?.bool != true {
                                Button("Activate") { Task { await activate(device.trackID) } }
                                    .buttonStyle(.borderless)
                            }
                        }
                        .swipeActions(edge: .trailing) {
                            Button("Rename") {
                                renaming = device
                                renameText = device["name"]?.string ?? ""
                            }
                            Button("Forget", role: .destructive) { Task { await forget(device.trackID) } }
                        }
                    }
                }

                Section("Pairing") {
                    Button("Create a one-time pairing code") { Task { await makeCode() } }
                    if let pairing {
                        LabeledContent("Code", value: pairing["code"]?.string ?? "")
                        if let hint = pairing["hint"]?.string {
                            Text(hint).font(.caption).foregroundStyle(tokens.dim)
                        }
                    }
                    SecureField("Pairing code from another device", text: $claimCode)
                        .textInputAutocapitalization(.never)
                    Button("Claim code") { Task { await claim() } }
                        .disabled(claimCode.isEmpty)
                }

                Section("Maintenance") {
                    Button("Remove stale devices") { Task { await run { try await app.client.cleanupDevices() } } }
                    Button("Forget all devices", role: .destructive) { Task { await run { try await app.client.clearDevices() } } }
                }

                Section("App passwords") {
                    if deviceTokens.isEmpty {
                        Text("No device tokens issued").foregroundStyle(tokens.dim)
                    }
                    ForEach(deviceTokens, id: \.trackID) { token in
                        HStack {
                            Text(token["prefix"]?.string ?? token["name"]?.string ?? "Token")
                            Spacer()
                            Button("Revoke", role: .destructive) { Task { await revoke(token.trackID) } }
                                .buttonStyle(.borderless)
                        }
                    }
                }
            }
            .navigationTitle("Devices")
            .refreshable { await load() }
            .sheet(item: $renaming) { device in
                NavigationStack {
                    Form {
                        TextField("Device name", text: $renameText)
                    }
                    .navigationTitle("Rename device")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) { Button("Cancel") { renaming = nil } }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Save") { Task { await rename(device.trackID) } }
                        }
                    }
                }
            }
        }
        .task { await load() }
    }

    private func load() async {
        do {
            devices = try await app.client.devices()
            deviceTokens = try await app.client.deviceTokens()
        } catch { app.show(error) }
    }

    private func activate(_ id: Int) async {
        await run { try await app.client.activateDevice(id) }
    }

    private func forget(_ id: Int) async {
        await run { try await app.client.forgetDevice(id) }
    }

    private func revoke(_ id: Int) async {
        await run { try await app.client.revokeDeviceToken(id) }
    }

    private func rename(_ id: Int) async {
        do {
            try await app.client.renameDevice(id, name: renameText)
            renaming = nil
            await load()
        } catch { app.show(error) }
    }

    private func makeCode() async {
        do {
            pairing = try await app.client.pairCode()
        } catch { app.show(error) }
    }

    private func claim() async {
        do {
            let result = try await app.client.claimPairCode(claimCode)
            app.show(result["error"]?.string ?? "Device paired")
            claimCode = ""
            await load()
        } catch { app.show(error) }
    }

    private func run(_ action: () async throws -> Void) async {
        do {
            try await action()
            await load()
        } catch { app.show(error) }
    }
}
