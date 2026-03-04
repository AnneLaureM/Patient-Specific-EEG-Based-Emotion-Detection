#!/bin/bash
# compile_final.sh - Compilation finale avec corrections

echo "📚 Compilation finale du papier"
echo "==============================="

cd /home/anne/Documents/Patient-Specific-EEG-Based-Emotion-Detection/paper

# Nettoyer
echo "🧹 Nettoyage..."
rm -rf build/
mkdir -p build

# Vérifier que les figures existent
echo "🔍 Vérification des figures..."
for fig in figure2_som_patient.png figure3_confusion.png figure4_features.png figure5_timeline.png figure6_connectivity.png figure7_spectral.png; do
    if [ -f "figures/$fig" ]; then
        echo "   ✅ $fig"
    else
        echo "   ⚠️  $fig manquante"
    fi
done

# Pass 1
echo "📄 Pass 1/4..."
pdflatex -output-directory=build main.tex > build/pass1.log

# Pass 2 (bibliographie)
echo "📚 Pass 2/4 (bibliographie)..."
bibtex build/main > build/bib.log

# Pass 3
echo "📄 Pass 3/4..."
pdflatex -output-directory=build main.tex > build/pass3.log

# Pass 4
echo "📄 Pass 4/4..."
pdflatex -output-directory=build main.tex > build/pass4.log

# Copier le PDF
cp build/main.pdf .

# Vérifier les warnings
echo ""
echo "⚠️  Warnings restants (max 5):"
grep -i warning build/main.log | tail -5 | sed 's/^/   /'

echo ""
echo "✅ Compilation terminée!"
echo "📁 PDF: $(pwd)/main.pdf"

# Ouvrir le PDF
if command -v evince &> /dev/null; then
    evince main.pdf &
elif command -v xdg-open &> /dev/null; then
    xdg-open main.pdf &
else
    echo "📁 Ouvrez manuellement: main.pdf"
fi