/** Tiny IndexedDB wrapper used for offline track blobs.
 */

// TODO: rename
export const dbName = "flufimusic";

export function open(store: string): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(dbName, 1);

        req.onupgradeneeded = (event) => {
            const db = (event.target as IDBOpenDBRequest).result;
            if (!db.objectStoreNames.contains(store)) {
                db.createObjectStore(store);
            }

            if (!db.objectStoreNames.contains("session")) {
                db.createObjectStore("session");
            }
        };

        req.onsuccess = (event) => {
            resolve((event.target as IDBOpenDBRequest).result);
        };

        req.onerror = (event) => {
            const db = (event.target as IDBOpenDBRequest).result;
            if (!db.objectStoreNames.contains(store)) {
                db.createObjectStore(store);
            }

            reject(req.error)
        };
    });
}

export async function set<T>(key: IDBValidKey, value: T, storeName: string): Promise<void> {
    const db = await open(storeName);
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readwrite");
        transaction.objectStore(storeName).put(value, key);
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
        transaction.onabort = () => reject(transaction.error);
    });
}

export async function get<T>(key: IDBValidKey, storeName: string): Promise<T | undefined> {
    const db = await open(storeName);
    const transaction = db.transaction(storeName, "readonly");
    const store = transaction.objectStore(storeName);

    return new Promise((resolve, reject) => {
        const request = store.get(key);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

export async function del(key: IDBValidKey, storeName: string): Promise<void> {
    const db = await open(storeName);
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, "readwrite");
        transaction.objectStore(storeName).delete(key);
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
        transaction.onabort = () => reject(transaction.error);
    });
}

export async function keys(storeName: string): Promise<IDBValidKey[]> {
    const db = await open(storeName);
    return new Promise((resolve, reject) => {
        const request = db.transaction(storeName, "readonly")
            .objectStore(storeName).getAllKeys();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

open("session");
