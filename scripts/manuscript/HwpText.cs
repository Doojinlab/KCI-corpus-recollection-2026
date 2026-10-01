using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Text;

// HWP 5.0 text extractor (no external dependencies).
// Reads the OLE compound file, inflates BodyText/SectionN, and prints PARA_TEXT records.
// Body paragraphs are indented with 2 spaces, nested paragraphs (footnotes, table cells, captions) with 6.
// Controls: [표·그림] = drawing/table, [각주] = footnote/endnote, {번호} = auto number, \t = tab.
public static class HwpText
{
    class DirEntry { public string Name; public int Type; public int Left, Right, Child; public uint Start; public ulong Size; }

    static byte[] data;
    static int secSize, miniSecSize;
    static uint miniCutoff;
    static List<uint> fat;
    static List<uint> miniFat;
    static List<DirEntry> dirs;
    static byte[] miniStream;
    static Dictionary<string, int> paths;
    static HashSet<int> seen;

    static uint U32(byte[] b, int o) { return BitConverter.ToUInt32(b, o); }
    static ushort U16(byte[] b, int o) { return BitConverter.ToUInt16(b, o); }
    static bool End(uint s) { return s == 0xFFFFFFFE || s == 0xFFFFFFFF; }

    static byte[] ReadFatChain(uint start, long size)
    {
        MemoryStream ms = new MemoryStream();
        uint s = start; int guard = 0;
        while (!End(s) && guard++ < 5000000)
        {
            long off = (long)(s + 1) * secSize;
            if (off >= data.Length) break;
            int n = (int)Math.Min(secSize, data.Length - off);
            ms.Write(data, (int)off, n);
            if (s >= fat.Count) break;
            s = fat[(int)s];
        }
        byte[] r = ms.ToArray();
        if (size >= 0 && r.Length > size) Array.Resize(ref r, (int)size);
        return r;
    }

    static byte[] ReadMiniChain(uint start, long size)
    {
        MemoryStream ms = new MemoryStream();
        uint s = start; int guard = 0;
        while (!End(s) && guard++ < 5000000)
        {
            long off = (long)s * miniSecSize;
            if (off >= miniStream.Length) break;
            int n = (int)Math.Min(miniSecSize, miniStream.Length - off);
            ms.Write(miniStream, (int)off, n);
            if (s >= miniFat.Count) break;
            s = miniFat[(int)s];
        }
        byte[] r = ms.ToArray();
        if (r.Length > size) Array.Resize(ref r, (int)size);
        return r;
    }

    static void Load(string path)
    {
        data = File.ReadAllBytes(path);
        fat = new List<uint>(); miniFat = new List<uint>(); dirs = new List<DirEntry>();
        paths = new Dictionary<string, int>(); seen = new HashSet<int>();
        secSize = 1 << U16(data, 0x1E);
        miniSecSize = 1 << U16(data, 0x20);
        uint firstDir = U32(data, 0x30);
        miniCutoff = U32(data, 0x38);
        uint firstMiniFat = U32(data, 0x3C);
        uint numMiniFat = U32(data, 0x40);
        uint firstDifat = U32(data, 0x44);
        uint numDifat = U32(data, 0x48);

        List<uint> fatSecs = new List<uint>();
        for (int i = 0; i < 109; i++) { uint v = U32(data, 0x4C + i * 4); if (!End(v)) fatSecs.Add(v); }
        uint d = firstDifat; int g = 0;
        while (!End(d) && g++ < (int)numDifat + 10)
        {
            int off = (int)((d + 1) * (uint)secSize);
            int per = secSize / 4 - 1;
            for (int i = 0; i < per; i++) { uint v = U32(data, off + i * 4); if (!End(v)) fatSecs.Add(v); }
            d = U32(data, off + per * 4);
        }
        foreach (uint fs in fatSecs)
        {
            long off = (long)(fs + 1) * secSize;
            if (off + secSize > data.Length) continue;
            for (int i = 0; i < secSize / 4; i++) fat.Add(U32(data, (int)off + i * 4));
        }

        byte[] dirBytes = ReadFatChain(firstDir, -1);
        for (int i = 0; i + 128 <= dirBytes.Length; i += 128)
        {
            DirEntry e = new DirEntry();
            int nameLen = U16(dirBytes, i + 0x40);
            e.Name = nameLen >= 2 ? Encoding.Unicode.GetString(dirBytes, i, Math.Min(64, nameLen) - 2) : "";
            e.Type = dirBytes[i + 0x42];
            e.Left = (int)U32(dirBytes, i + 0x44);
            e.Right = (int)U32(dirBytes, i + 0x48);
            e.Child = (int)U32(dirBytes, i + 0x4C);
            e.Start = U32(dirBytes, i + 0x74);
            e.Size = BitConverter.ToUInt64(dirBytes, i + 0x78);
            if (secSize == 512) e.Size &= 0xFFFFFFFFUL;
            dirs.Add(e);
        }
        if (numMiniFat > 0 && !End(firstMiniFat))
        {
            byte[] mf = ReadFatChain(firstMiniFat, -1);
            for (int i = 0; i + 4 <= mf.Length; i += 4) miniFat.Add(U32(mf, i));
        }
        miniStream = ReadFatChain(dirs[0].Start, (long)dirs[0].Size);
        Walk(0, "");
    }

    static void Walk(int id, string parent)
    {
        if (id < 0 || id >= dirs.Count || seen.Contains(id)) return;
        seen.Add(id);
        DirEntry e = dirs[id];
        Walk(e.Left, parent);
        string p = parent.Length == 0 ? e.Name : parent + "/" + e.Name;
        if (e.Type != 5) paths[p] = id;
        if (e.Type == 1 || e.Type == 5) Walk(e.Child, e.Type == 5 ? "" : p);
        Walk(e.Right, parent);
    }

    static byte[] GetStream(string path)
    {
        int id;
        if (!paths.TryGetValue(path, out id)) return null;
        DirEntry e = dirs[id];
        if (e.Size < miniCutoff) return ReadMiniChain(e.Start, (long)e.Size);
        return ReadFatChain(e.Start, (long)e.Size);
    }

    static byte[] Inflate(byte[] raw)
    {
        using (MemoryStream ms = new MemoryStream(raw))
        using (DeflateStream ds = new DeflateStream(ms, CompressionMode.Decompress))
        using (MemoryStream o = new MemoryStream()) { ds.CopyTo(o); return o.ToArray(); }
    }

    static string DecodeParaText(byte[] b, int off, int size)
    {
        StringBuilder t = new StringBuilder();
        int n = size / 2; int i = 0;
        while (i < n)
        {
            int c = U16(b, off + i * 2);
            if (c >= 32) { t.Append((char)c); i += 1; continue; }
            switch (c)
            {
                case 9: t.Append('\t'); i += 8; break;
                case 10: t.Append(' '); i += 1; break;
                case 13: i += 1; break;
                case 24: t.Append('-'); i += 1; break;
                case 30: case 31: t.Append(' '); i += 1; break;
                case 0: case 25: case 26: case 27: case 28: case 29: i += 1; break;
                case 11: t.Append("[표·그림]"); i += 8; break;
                case 17: t.Append("[각주]"); i += 8; break;
                case 18: t.Append("{번호}"); i += 8; break;
                default: i += 8; break;
            }
        }
        return t.ToString();
    }

    public static string Extract(string path)
    {
        Load(path);
        byte[] fh = GetStream("FileHeader");
        if (fh == null) throw new Exception("FileHeader not found: not an HWP 5.0 file?");
        bool compressed = (U32(fh, 36) & 1) != 0;
        StringBuilder sb = new StringBuilder();
        for (int s = 0; ; s++)
        {
            byte[] raw = GetStream("BodyText/Section" + s);
            if (raw == null) break;
            byte[] body = compressed ? Inflate(raw) : raw;
            sb.Append("=== BodyText/Section" + s + " ===\n");
            int p = 0;
            while (p + 4 <= body.Length)
            {
                uint h = U32(body, p); p += 4;
                int tag = (int)(h & 0x3FF);
                int level = (int)((h >> 10) & 0x3FF);
                int size = (int)((h >> 20) & 0xFFF);
                if (size == 0xFFF) { size = (int)U32(body, p); p += 4; }
                if (p + size > body.Length) break;
                if (tag == 67)
                {
                    string text = DecodeParaText(body, p, size);
                    sb.Append(level <= 1 ? "  " : "      ").Append(text).Append('\n');
                }
                p += size;
            }
        }
        return sb.ToString();
    }
}
