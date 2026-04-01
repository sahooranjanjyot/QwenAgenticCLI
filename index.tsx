import React, { useState } from 'react';
import { render, Text, Box, useInput, useApp } from 'ink';
import chalk from 'chalk';

const AssistantCLI = () => {
    const { exit } = useApp();
    const [input, setInput] = useState('');
    const [history, setHistory] = useState([
        { role: 'system', content: 'Welcome to your custom Open-Source AI Terminal! What would you like to build today?' }
    ]);

    useInput((char, key) => {
        if (key.return) {
            if (input.trim().toLowerCase() === '/exit' || input.trim().toLowerCase() === 'quit') {
                exit();
                return;
            }
            if (input.trim() !== '') {
                setHistory(prev => [...prev, { role: 'user', content: input }]);
                setInput('');
                
                // This is where you would natively ping your own AI API!
                setTimeout(() => {
                    setHistory(prev => [...prev, { role: 'assistant', content: `[Thinking...] I am a mock AI! You just said: "${input}". 
You can easily connect me to the free Google Gemini developer API right here!` }]);
                }, 500);
            }
        } else if (key.backspace || key.delete) {
            setInput(prev => prev.slice(0, -1));
        } else if (key.ctrl && char === 'c') {
            exit();
        } else if (char) {
            setInput(prev => prev + char);
        }
    });

    return (
        <Box flexDirection="column" padding={1}>
            <Box borderStyle="round" borderColor="cyan" padding={1} flexDirection="column">
                <Text color="cyan" bold>🧠 OpenCLI Agent Terminal v1.0.0</Text>
                <Text color="gray">Inspired by Anthropic's leaked codebase. Built purely with React & Ink entirely inside your terminal.</Text>
            </Box>
            
            <Box flexDirection="column" marginY={1}>
                {history.map((msg, index) => (
                    <Box key={index} marginY={0}>
                        <Text color={msg.role === 'user' ? 'green' : (msg.role === 'system' ? 'yellow' : 'magenta')} bold>
                            {msg.role === 'user' ? '❯ You: ' : (msg.role === 'system' ? '💻 System: ' : '✨ Assistant: ')}
                        </Text>
                        <Text color="white">{msg.content}</Text>
                    </Box>
                ))}
            </Box>

            <Box marginTop={1}>
                <Text color="cyan" bold>✏️  Type a message (or type /exit): </Text>
                <Text>{input}</Text>
                <Text color="white" bold>█</Text>
            </Box>
        </Box>
    );
};

console.clear();
render(<AssistantCLI />);
