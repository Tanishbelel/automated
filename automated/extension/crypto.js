/**
 * Crypto Utility for Local File Encryption/Decryption
 * Uses Web Crypto API with AES-256-GCM
 */

const CryptoUtils = {
    // Configuration
    ALGORITHM: 'AES-GCM',
    KEY_LENGTH: 256,
    SALT_LENGTH: 16,
    IV_LENGTH: 12,
    PBKDF2_ITERATIONS: 100000,

    /**
     * Generate a random salt
     */
    generateSalt() {
        return crypto.getRandomValues(new Uint8Array(this.SALT_LENGTH));
    },

    /**
     * Generate a random IV (Initialization Vector)
     */
    generateIV() {
        return crypto.getRandomValues(new Uint8Array(this.IV_LENGTH));
    },

    /**
     * Derive a cryptographic key from password using PBKDF2
     */
    async deriveKey(password, salt) {
        const encoder = new TextEncoder();
        const passwordBuffer = encoder.encode(password);

        // Import password as a key
        const passwordKey = await crypto.subtle.importKey(
            'raw',
            passwordBuffer,
            'PBKDF2',
            false,
            ['deriveBits', 'deriveKey']
        );

        // Derive the actual encryption key
        const derivedKey = await crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: salt,
                iterations: this.PBKDF2_ITERATIONS,
                hash: 'SHA-256'
            },
            passwordKey,
            { name: this.ALGORITHM, length: this.KEY_LENGTH },
            false,
            ['encrypt', 'decrypt']
        );

        return derivedKey;
    },

    /**
     * Encrypt file data with password
     * @param {ArrayBuffer} data - File data to encrypt
     * @param {string} password - User's password
     * @returns {ArrayBuffer} - Encrypted data with salt and IV prepended
     */
    async encrypt(data, password) {
        const salt = this.generateSalt();
        const iv = this.generateIV();
        const key = await this.deriveKey(password, salt);

        const encryptedData = await crypto.subtle.encrypt(
            { name: this.ALGORITHM, iv: iv },
            key,
            data
        );

        // Combine: Salt (16) + IV (12) + Encrypted Data
        const result = new Uint8Array(salt.length + iv.length + encryptedData.byteLength);
        result.set(salt, 0);
        result.set(iv, salt.length);
        result.set(new Uint8Array(encryptedData), salt.length + iv.length);

        return result.buffer;
    },

    /**
     * Decrypt file data with password
     * @param {ArrayBuffer} encryptedData - Encrypted data with salt and IV
     * @param {string} password - User's password
     * @returns {ArrayBuffer} - Decrypted original data
     */
    async decrypt(encryptedData, password) {
        const dataArray = new Uint8Array(encryptedData);

        // Extract salt, IV, and encrypted content
        const salt = dataArray.slice(0, this.SALT_LENGTH);
        const iv = dataArray.slice(this.SALT_LENGTH, this.SALT_LENGTH + this.IV_LENGTH);
        const data = dataArray.slice(this.SALT_LENGTH + this.IV_LENGTH);

        const key = await this.deriveKey(password, salt);

        const decryptedData = await crypto.subtle.decrypt(
            { name: this.ALGORITHM, iv: iv },
            key,
            data
        );

        return decryptedData;
    },

    /**
     * Read file as ArrayBuffer
     */
    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsArrayBuffer(file);
        });
    },

    /**
     * Download data as file
     */
    downloadFile(data, filename, mimeType = 'application/octet-stream') {
        const blob = new Blob([data], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    /**
     * Get original filename from encrypted filename
     */
    getOriginalFilename(encryptedFilename) {
        if (encryptedFilename.endsWith('.enc')) {
            return encryptedFilename.slice(0, -4);
        }
        return encryptedFilename + '.decrypted';
    },

    /**
     * Get encrypted filename from original
     */
    getEncryptedFilename(originalFilename) {
        return originalFilename + '.enc';
    }
};
