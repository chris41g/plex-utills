#!/bin/bash

echo "🔧 Fixing the specific config access issue in app/module.py..."

if [ -f "app/module.py" ]; then
    echo "📝 Fixing config attribute access in app/module.py..."
    
    # Fix the specific lines that are causing the error
    # These need to access config as a list/tuple, not as an object
    sed -i 's/config\.manualplexpath/config[0].manualplexpath/g' app/module.py
    sed -i 's/config\.manualplexpathfield/config[0].manualplexpathfield/g' app/module.py
    
    echo "✅ Fixed app/module.py config access"
else
    echo "⚠️  app/module.py not found"
fi

echo "🎉 Fix complete!"
echo "🔄 Restart your Plex-Utills container."
echo "📋 This should resolve the 'list' object has no attribute 'manualplexpath' error!"
