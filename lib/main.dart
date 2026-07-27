import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'features/triage/data/triage_repository.dart';
import 'features/triage/presentation/state/triage_state_manager.dart';
import 'presentation/web_dashboard.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => TriageStateManager(TriageRepository()),
        ),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MaruCure Silicosis Triage Engine',
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.teal,
        scaffoldBackgroundColor: const Color(0xFF0b0f19),
      ),
      home: WebDashboard(),
    );
  }
}
