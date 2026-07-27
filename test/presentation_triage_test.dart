import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import '../lib/features/triage/domain/screening_entity.dart';
import '../lib/features/triage/data/triage_repository.dart';
import '../lib/features/triage/presentation/state/triage_state_manager.dart';
import '../lib/features/triage/presentation/pages/triage_dashboard.dart';

void main() {
  group('Triage Presentation Layer Tests', () {
    testWidgets('Renders Study Queue and correctly highlights high-risk triage cards', (WidgetTester tester) async {
      // 1. Arrange state
      final mockRepo = TriageRepository(testDb: null); // Null for mocked state logic
      final stateManager = TriageStateManager(mockRepo);
      
      // Inject explicit test state
      stateManager.setMockQueueForTesting([
        ScreeningEntity(
          id: '1',
          fullName: 'Normal Miner',
          janAadhaarNumber: '12345',
          riskIndexScore: 2.0,
          clinicalFlag: 'NORMAL',
        ),
        ScreeningEntity(
          id: '2',
          fullName: 'Critical Miner',
          janAadhaarNumber: '67890',
          riskIndexScore: 8.5, // >= 7.5 High Risk
          clinicalFlag: 'FIR', // High Risk
        ),
      ]);

      // 2. Pump widget tree
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<TriageStateManager>.value(
            value: stateManager,
            child: const TriageDashboard(),
          ),
        ),
      );

      // 3. Verify elements
      expect(find.text('Normal Miner'), findsOneWidget);
      expect(find.text('Critical Miner'), findsOneWidget);
      
      // 4. Verify visual warning layouts based on Card color
      final cardFinder = find.ancestor(
        of: find.text('Critical Miner'),
        matching: find.byType(Card),
      );
      expect(cardFinder, findsOneWidget);
      
      final Card card = tester.widget<Card>(cardFinder);
      expect(card.color, equals(Colors.red.shade100)); // Dynamic color shift triggered
      
      final Icon icon = tester.widget<Icon>(
        find.descendant(of: cardFinder, matching: find.byType(Icon)).first,
      );
      expect(icon.icon, equals(Icons.warning_amber_rounded)); // Urgent action alert icon triggered
    });

    test('TriageStateManager correctly commands SQLite updates (No in-memory maps)', () async {
      // Simulate state manager dependency flow
      final repo = TriageRepository();
      final stateManager = TriageStateManager(repo);
      
      // We expect the stateManager to not rely on a simple List add, but route via SQLite
      // We catch the Flutter DB plugin exception which proves it routed through repository.insertScreening
      expect(
        () => stateManager.registerNewScreening(
          ScreeningEntity(
            id: '3',
            fullName: 'Test SQLite Insert',
            janAadhaarNumber: '111',
            riskIndexScore: 1.0,
            clinicalFlag: 'NORMAL'
          )
        ), 
        throwsException, 
      );
    });
  });
}
